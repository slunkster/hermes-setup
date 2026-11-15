"""Resumable full-frame motion and person measurements; no editorial classification."""
import argparse
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import time
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

FPS = 25
WIDTH, HEIGHT = 640, 360
DETECT_EVERY = 12
SCORE_THRESHOLD = 0.15
NMS_THRESHOLD = 0.45
B_OFFSET_FRAMES = 526  # B native = A reference - 21.04 seconds (provisional).
SET_WINDOWS = ((381, 3568), (4654, 6878), (8169, 10737), (13408, 17588))


@dataclass(frozen=True)
class SourceSpec:
    path: Path
    start_frame: int
    end_frame: int | None = None


@dataclass(frozen=True)
class Chunk:
    camera: str
    start_frame: int
    end_frame: int
    source: Path
    source_start_frame: int

    @property
    def expected_frames(self):
        return self.end_frame - self.start_frame

    @property
    def key(self):
        return f"{self.camera}_{self.start_frame:09d}_{self.end_frame:09d}"


def seconds_to_frames(seconds):
    """Floor a duration to the integer 25 fps grid without floating-point drift."""
    return int((Decimal(str(seconds)) * FPS).to_integral_value(rounding=ROUND_FLOOR))


def frame_seconds(frame):
    return f"{Decimal(int(frame)) / FPS:.2f}"


def camera_sources(camera, media_dir):
    if camera == "A":
        names = ("A089C001_260904_DJ0B.MOV", "A089C002_260904_DJ0B.MOV")
        split = seconds_to_frames("11040.48")
    elif camera == "B":
        names = ("S1310001.MP4", "S1310002.MP4")
        split = seconds_to_frames("11040.96")
    else:
        raise ValueError(f"unknown camera: {camera}")
    return [SourceSpec(Path(media_dir) / names[0], 0, split),
            SourceSpec(Path(media_dir) / names[1], split)]


def analysis_windows(camera):
    if camera not in ("A", "B"):
        raise ValueError(f"unknown camera: {camera}")
    margin = (13 if camera == "B" else 10) * FPS
    shift = B_OFFSET_FRAMES if camera == "B" else 0
    return [(max(0, start * FPS - margin - shift), end * FPS + margin - shift)
            for start, end in SET_WINDOWS]


def map_chunks(camera, windows, sources, chunk_frames):
    if not 1 <= chunk_frames <= 300 * FPS:
        raise ValueError("chunk size must be 1..7500 frames (<=300 seconds)")
    result = []
    for start, end in windows:
        cursor = start
        while cursor < end:
            source = next((s for s in sources if s.start_frame <= cursor and
                           (s.end_frame is None or cursor < s.end_frame)), None)
            if source is None:
                raise ValueError(f"unmapped source frame {camera}:{cursor}")
            stop = min(end, cursor + chunk_frames,
                       source.end_frame if source.end_frame is not None else end)
            result.append(Chunk(camera, cursor, stop, source.path, cursor - source.start_frame))
            cursor = stop
    return result


def nms(boxes, scores, threshold=NMS_THRESHOLD):
    """Person-only NMS; no area/ROI filtering or obstruction inference."""
    order = np.argsort(-scores, kind="stable")
    chosen = []
    while len(order):
        index = int(order[0])
        chosen.append(index)
        order = order[1:]
        if not len(order):
            break
        box, others = boxes[index], boxes[order]
        intersection = np.prod(np.maximum(0, np.minimum(box[2:], others[:, 2:]) -
                                           np.maximum(box[:2], others[:, :2])), axis=1)
        area = np.prod(np.maximum(0, box[2:] - box[:2]))
        areas = np.prod(np.maximum(0, others[:, 2:] - others[:, :2]), axis=1)
        iou = intersection / np.maximum(area + areas - intersection, 1e-12)
        order = order[iou < threshold]
    return chosen


def small_luma(rgb):
    return np.asarray(Image.fromarray(rgb).convert("L").resize(
        (160, 90), Image.Resampling.BILINEAR))


def motion_score(current, previous):
    difference = np.abs(current.astype(np.int16) - previous.astype(np.int16))
    return float(np.mean(difference > 35))


def decode_people(raw, grid, strides, ratio, width=WIDTH, height=HEIGHT):
    """Decode the official raw YOLOX export; COCO person class is column 5."""
    prediction = np.asarray(raw, dtype=np.float32).copy()
    if prediction.ndim != 2 or prediction.shape[1] != 85 or len(prediction) != len(grid):
        raise ValueError(f"expected raw Nx85 YOLOX output, got {prediction.shape}")
    if not np.isfinite(prediction).all():
        raise ValueError("YOLOX output contains non-finite values")
    prediction[:, :2] = (prediction[:, :2] + grid) * strides
    prediction[:, 2:4] = np.exp(prediction[:, 2:4]) * strides
    scores = prediction[:, 4] * prediction[:, 5]
    boxes = np.concatenate((prediction[:, :2] - prediction[:, 2:4] / 2,
                            prediction[:, :2] + prediction[:, 2:4] / 2), axis=1) / ratio
    boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, width)
    boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, height)
    valid = ((scores >= SCORE_THRESHOLD) & (boxes[:, 2] > boxes[:, 0]) &
             (boxes[:, 3] > boxes[:, 1]))
    boxes, scores = boxes[valid], scores[valid]
    return [{"box": (boxes[index] / [width, height, width, height]).tolist(),
             "score": float(scores[index])}
            for index in nms(boxes, scores)]


class YoloXDetector:
    """Official YOLOX tiny 416 export, matching the tested BGR/114-pad pipeline."""

    def __init__(self, model, threads=4):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        self.session = ort.InferenceSession(str(model), sess_options=options,
                                           providers=["CPUExecutionProvider"])
        model_input = self.session.get_inputs()[0]
        if model_input.shape != [1, 3, 416, 416]:
            raise ValueError(f"expected official [1,3,416,416] model, got {model_input.shape}")
        self.input_name = model_input.name
        self.input_height, self.input_width = model_input.shape[2:]
        grids, strides = [], []
        for stride in (8, 16, 32):
            x, y = np.meshgrid(np.arange(self.input_width // stride),
                               np.arange(self.input_height // stride))
            grid = np.stack((x, y), axis=2).reshape(-1, 2)
            grids.append(grid)
            strides.append(np.full((len(grid), 1), stride, dtype=np.float32))
        self.grid = np.concatenate(grids)
        self.strides = np.concatenate(strides)

    def detect(self, rgb):
        height, width = rgb.shape[:2]
        ratio = min(self.input_width / width, self.input_height / height)
        resized = np.asarray(Image.fromarray(rgb).resize(
            (int(width * ratio), int(height * ratio)), Image.Resampling.BILINEAR))[:, :, ::-1]
        image = np.full((self.input_height, self.input_width, 3), 114, dtype=np.float32)
        image[:resized.shape[0], :resized.shape[1]] = resized
        tensor = np.ascontiguousarray(image.transpose(2, 0, 1)[None])
        output = self.session.run(None, {self.input_name: tensor})[0]
        if output.ndim != 3 or output.shape[0] != 1:
            raise ValueError(f"unexpected YOLOX output shape: {output.shape}")
        return decode_people(output[0], self.grid, self.strides, ratio, width, height)


@dataclass(frozen=True)
class DecodePlan:
    command: list
    preroll: int
    predecessor_command: list | None = None


def ffmpeg_command(ffmpeg, source, start_frame, frame_count, hwaccel):
    command = [str(ffmpeg), "-hide_banner", "-nostdin", "-loglevel", "warning", "-xerror"]
    if hwaccel != "none":
        command += ["-hwaccel", hwaccel]
    command += ["-ss", frame_seconds(start_frame), "-err_detect", "explode",
                "-i", str(source), "-map", "0:v:0", "-an", "-sn", "-dn",
                "-vf", f"scale={WIDTH}:{HEIGHT}:flags=bilinear,format=rgb24",
                "-fps_mode", "passthrough", "-frames:v", str(frame_count),
                "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    return command


def make_decode_plan(chunk, sources, ffmpeg, hwaccel):
    preroll = int(chunk.source_start_frame > 0)
    command = ffmpeg_command(ffmpeg, chunk.source, chunk.source_start_frame - preroll,
                             chunk.expected_frames + preroll, hwaccel)
    previous_command = None
    if not preroll and chunk.start_frame > 0:
        previous_chunk = map_chunks(chunk.camera,
                                    [(chunk.start_frame - 1, chunk.start_frame)], sources, 1)[0]
        previous_command = ffmpeg_command(ffmpeg, previous_chunk.source,
                                          previous_chunk.source_start_frame, 1, hwaccel)
    return DecodePlan(command, preroll, previous_command)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter,
        epilog="Outputs: one JSONL sample per 12 native frames (including empty people lists);\n"
               "NPZ motion arrays have one row per native 25 fps frame, with exact integer indexes.\n"
               "All intervals are half-open. B reference timestamps use provisional A=B+21.04s.\n"
               "--probe limits each camera to its first N seconds. --source requires --probe.\n"
               "Only true recording frame zero lacks a predecessor (motion_valid=False).")
    parser.add_argument("--camera", choices=("A", "B", "all"), default="all")
    parser.add_argument("--media-dir", type=Path, default=Path("G:/Active Media/Blues Fest"))
    parser.add_argument("--ffmpeg", default="C:/Users/Siim Alve/AppData/Local/hermes/tools/"
                                          "ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe")
    parser.add_argument("--model", type=Path, default=Path(__file__).resolve().parent / "yolox_tiny.onnx")
    parser.add_argument("--out-dir", type=Path, default=Path.home() / "Hermes/bluesfest/v2/analysis")
    parser.add_argument("--hwaccel", choices=("d3d11va", "none"), default="d3d11va")
    parser.add_argument("--probe", type=Decimal, metavar="SECONDS", help="first N seconds per selected camera")
    parser.add_argument("--source", type=Path, help="custom single 25fps source; time zero; default camera A")
    parser.add_argument("--chunk-seconds", type=Decimal, default=Decimal(300))
    parser.add_argument("--ort-threads", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="print chunk plan without decoding or model load")
    return parser


def make_plan(args):
    if not args.chunk_seconds.is_finite() or not Decimal(0) < args.chunk_seconds <= 300:
        raise ValueError("--chunk-seconds must be >0 and <=300")
    chunk_frames = seconds_to_frames(args.chunk_seconds)
    if not chunk_frames:
        raise ValueError("--chunk-seconds must cover at least one frame")
    probe_frames = None
    if args.probe is not None:
        if not args.probe.is_finite() or args.probe <= 0:
            raise ValueError("--probe must be a finite positive duration")
        probe_frames = seconds_to_frames(args.probe)
        if not probe_frames:
            raise ValueError("--probe must cover at least one 25 fps frame")
    if args.ort_threads < 1:
        raise ValueError("--ort-threads must be positive")
    if args.source:
        if probe_frames is None:
            raise ValueError("--source requires an explicit --probe duration")
        camera = "A" if args.camera == "all" else args.camera
        return map_chunks(camera, [(0, probe_frames)], [SourceSpec(args.source, 0)], chunk_frames)
    result = []
    for camera in (("A", "B") if args.camera == "all" else (args.camera,)):
        windows = analysis_windows(camera)
        if probe_frames is not None:
            windows = [(windows[0][0], min(windows[0][0] + probe_frames, windows[0][1]))]
        result.extend(map_chunks(camera, windows, camera_sources(camera, args.media_dir), chunk_frames))
    return result


def read_exact(stream, size):
    """Read a complete raw frame; EOF is clean only before the first byte."""
    if size <= 0:
        raise ValueError("read size must be positive")
    parts = bytearray()
    while len(parts) < size:
        block = stream.read(size - len(parts))
        if not block:
            if not parts:
                return b""
            raise EOFError(f"truncated frame: {len(parts)} of {size} bytes")
        parts.extend(block)
    return bytes(parts)


def decode_frames(command, stderr_path, expected_frames):
    """Yield complete RGB frames, then assert exit status AND exact decoded count.

    stderr goes directly to disk, never to an unread pipe. Closing this generator
    (including detector exceptions) terminates the decoder rather than orphaning it.
    """
    with Path(stderr_path).open("wb") as error_log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=error_log, bufsize=0)
        count = 0
        try:
            while True:
                data = read_exact(process.stdout, WIDTH * HEIGHT * 3)
                if not data:
                    break
                count += 1
                if count > expected_frames:
                    raise RuntimeError(f"decoder emitted more than {expected_frames} frames")
                yield np.frombuffer(data, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)
            returncode = process.wait(timeout=30)
            if returncode != 0 or count != expected_frames:
                raise RuntimeError(f"decoder exit={returncode}, frames={count}, "
                                   f"expected={expected_frames}; see {stderr_path}")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=30)
            process.stdout.close()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def chunk_paths(out_dir, chunk):
    base = Path(out_dir) / chunk.camera / chunk.key
    return {"meta": base.with_suffix(".meta.json"),
            "people": base.with_suffix(".people.jsonl"),
            "motion": base.with_suffix(".motion.npz"),
            "stderr": base.with_suffix(".stderr.log"),
            "predecessor_stderr": base.with_suffix(".predecessor.stderr.log")}


def chunk_is_complete(chunk, paths, signature):
    """Never trust a completion flag alone or silently reuse a different analysis."""
    try:
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            return False
        if not (meta.get("complete") is True and meta.get("signature") == signature
                and meta.get("frame_count") == chunk.expected_frames
                and meta.get("ffmpeg_exit_code") == 0):
            return False
        for name in ("people", "motion"):
            if file_hash(paths[name]) != meta["sha256"][name]:
                return False
        with np.load(paths["motion"], allow_pickle=False) as arrays:
            expected = np.arange(chunk.start_frame, chunk.end_frame, dtype=np.int64)
            if not np.array_equal(arrays["frame_index"], expected):
                return False
            if any(len(arrays[name]) != len(expected) for name in (
                    "motion_score", "motion_valid", "time_seconds", "source_frame_index",
                    "reference_frame_index", "reference_time_seconds")):
                return False
        return True
    except (OSError, ValueError, KeyError, EOFError, TypeError):
        return False


def run_chunk(chunk, out_dir, detector, command, signature, preroll=0,
              previous=None, progress=None):
    """Transactional output: data files first, complete metadata last.

    ``preroll=1`` includes the preceding source frame in the same decode; at
    a recorder split, supply the previous file's final luma as ``previous``.
    At true recording frame zero there is no predecessor: motion_valid=False.
    """
    paths = chunk_paths(out_dir, chunk)
    paths["meta"].parent.mkdir(parents=True, exist_ok=True)
    if chunk_is_complete(chunk, paths, signature):
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        return dict(meta, resumed=True)
    if preroll not in (0, 1):
        raise ValueError("preroll must be zero or one frame")
    started = time.monotonic()
    meta = {"schema_version": 1, "complete": False, "signature": signature,
            "chunk": dict(asdict(chunk), source=str(chunk.source)),
            "fps": FPS, "expected_frames": chunk.expected_frames,
            "frame_count": 0, "decode_expected_frames": chunk.expected_frames + preroll,
            "preroll_frames": preroll, "ffmpeg_exit_code": None,
            "started_at": utc_now(), "command": command,
            "box_format": "normalized xyxy; ALL person candidates after NMS; no blocked label",
            "detection_every_frames": DETECT_EVERY,
            "score_threshold": SCORE_THRESHOLD, "nms_threshold": NMS_THRESHOLD}
    atomic_json(paths["meta"], meta)
    temporary_people = paths["people"].with_suffix(".jsonl.tmp")
    temporary_motion = paths["motion"].with_suffix(".npz.tmp")
    scores = np.zeros(chunk.expected_frames, dtype=np.float32)
    valid = np.zeros(chunk.expected_frames, dtype=np.bool_)
    count = samples = 0
    try:
        with closing(decode_frames(command, paths["stderr"],
                                   chunk.expected_frames + preroll)) as frames:
            if preroll:
                previous = small_luma(next(frames))
            with temporary_people.open("w", encoding="utf-8", newline="\n") as people_file:
                for index, rgb in enumerate(frames):
                    frame_index = chunk.start_frame + index
                    current = small_luma(rgb)
                    valid[index] = previous is not None
                    if previous is not None:
                        scores[index] = motion_score(current, previous)
                    previous = current
                    if frame_index % DETECT_EVERY == 0:
                        reference = frame_index + (B_OFFSET_FRAMES if chunk.camera == "B" else 0)
                        row = {"camera": chunk.camera, "frame_index": frame_index,
                               "time_seconds": frame_index / FPS,
                               "reference_frame_index": reference,
                               "reference_time_seconds": reference / FPS,
                               "source_frame_index": chunk.source_start_frame + index,
                               "people": detector.detect(rgb)}
                        people_file.write(json.dumps(row, allow_nan=False) + "\n")
                        samples += 1
                    count += 1
                    if progress is not None and (count % FPS == 0 or count == chunk.expected_frames):
                        progress(count, chunk.expected_frames)
                people_file.flush()
                os.fsync(people_file.fileno())
        if count != chunk.expected_frames:
            raise RuntimeError(f"processed {count} frames, expected {chunk.expected_frames}")
        indexes = np.arange(chunk.start_frame, chunk.end_frame, dtype=np.int64)
        reference = indexes + (B_OFFSET_FRAMES if chunk.camera == "B" else 0)
        with temporary_motion.open("wb") as motion_file:
            np.savez_compressed(motion_file, frame_index=indexes,
                                time_seconds=indexes / FPS,
                                source_frame_index=np.arange(chunk.source_start_frame,
                                                             chunk.source_start_frame + count),
                                reference_frame_index=reference,
                                reference_time_seconds=reference / FPS,
                                motion_score=scores, motion_valid=valid)
            motion_file.flush()
            os.fsync(motion_file.fileno())
        os.replace(temporary_people, paths["people"])
        os.replace(temporary_motion, paths["motion"])
        meta.update(complete=True, frame_count=count, detection_samples=samples,
                    ffmpeg_exit_code=0, decode_frame_count=count + preroll,
                    finished_at=utc_now(), elapsed_seconds=time.monotonic() - started,
                    sha256={name: file_hash(paths[name]) for name in ("people", "motion")})
        atomic_json(paths["meta"], meta)
        return meta
    except BaseException as error:
        meta.update(complete=False, frame_count=count, error=f"{type(error).__name__}: {error}",
                    failed_at=utc_now())
        atomic_json(paths["meta"], meta)
        raise
    finally:
        temporary_people.unlink(missing_ok=True)
        temporary_motion.unlink(missing_ok=True)


@contextmanager
def output_lock(out_dir):
    """OS-owned lock, automatically released after a crash; safe to resume."""
    with (Path(out_dir) / ".analysis.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if not lock.tell():
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError(f"another analyzer owns {out_dir}; use another --out-dir") from error
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def file_identity(path):
    path = Path(path).resolve(strict=True)
    stat = path.stat()
    return {"path": str(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def execute_analysis(args, chunks):
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with output_lock(out_dir):
        started = time.monotonic()
        status = {"schema_version": 1, "state": "starting", "pid": os.getpid(),
                  "started_at": utc_now(), "total_chunks": len(chunks),
                  "total_frames": sum(chunk.expected_frames for chunk in chunks),
                  "completed_chunks": 0, "completed_frames": 0, "resumed_chunks": 0,
                  "active_chunk": None, "active_frames": 0, "fps": FPS,
                  "hwaccel": args.hwaccel, "out_dir": str(out_dir),
                  "source_assumption": "25fps CFR; native integer frame indexes",
                  "sync_status": "provisional: B native=A reference-21.04s; extra B safety=3s"}

        def report(**updates):
            status.update(updates, updated_at=utc_now(), elapsed_seconds=time.monotonic() - started)
            atomic_json(out_dir / "status.json", status)

        report()
        try:
            executable = shutil.which(str(args.ffmpeg))
            if executable is None:
                raise FileNotFoundError(f"ffmpeg not found: {args.ffmpeg}")
            provenance = {"analyzer_sha256": file_hash(Path(__file__)),
                          "model_sha256": file_hash(args.model),
                          "ffmpeg": file_identity(executable), "hwaccel": args.hwaccel,
                          "ort_threads": args.ort_threads}
            # Validate every referenced file before beginning a long run.
            source_identities = {}
            for chunk in chunks:
                if chunk.source not in source_identities:
                    source_identities[chunk.source] = file_identity(chunk.source)
            detector = None
            for ordinal, chunk in enumerate(chunks, 1):
                sources = ([SourceSpec(args.source, 0)] if args.source else
                           camera_sources(chunk.camera, args.media_dir))
                decode = make_decode_plan(chunk, sources, executable, args.hwaccel)
                signature_data = dict(provenance, chunk=dict(asdict(chunk), source=str(chunk.source)),
                                      source=source_identities[chunk.source], decode=asdict(decode))
                if decode.predecessor_command:
                    predecessor_path = Path(decode.predecessor_command[
                        decode.predecessor_command.index("-i") + 1])
                    signature_data["predecessor_source"] = file_identity(predecessor_path)
                signature = hashlib.sha256(json.dumps(signature_data, sort_keys=True).encode()).hexdigest()
                paths = chunk_paths(out_dir, chunk)
                report(state="running", active_chunk=chunk.key, active_frames=0)
                print(f"[{ordinal}/{len(chunks)}] {chunk.key}: native "
                      f"{frame_seconds(chunk.start_frame)}..{frame_seconds(chunk.end_frame)}s "
                      f"({chunk.expected_frames} frames), {chunk.source.name}", flush=True)
                chunk_started = last_report = last_print = time.monotonic()

                def progress(count, total):
                    nonlocal last_report, last_print
                    now = time.monotonic()
                    if now - last_report >= 2 or count == total:
                        report(active_frames=count)
                        last_report = now
                    if now - last_print >= 10 or count == total:
                        speed = count / max(now - chunk_started, 1e-9)
                        print(f"  {chunk.key} {count}/{total} frames; {speed:.1f} fps", flush=True)
                        last_print = now

                if chunk_is_complete(chunk, paths, signature):
                    metadata = json.loads(paths["meta"].read_text(encoding="utf-8"))
                    metadata["resumed"] = True
                else:
                    if detector is None:
                        print("  loading official YOLOX tiny 416 on CPU", flush=True)
                        detector = YoloXDetector(args.model, args.ort_threads)
                    previous = None
                    if decode.predecessor_command:
                        paths["meta"].parent.mkdir(parents=True, exist_ok=True)
                        predecessor = list(decode_frames(decode.predecessor_command,
                                                        paths["predecessor_stderr"], 1))
                        previous = small_luma(predecessor[0])
                    metadata = run_chunk(chunk, out_dir, detector, decode.command, signature,
                                         decode.preroll, previous, progress)
                resumed = bool(metadata.get("resumed"))
                report(completed_chunks=status["completed_chunks"] + 1,
                       completed_frames=status["completed_frames"] + chunk.expected_frames,
                       resumed_chunks=status["resumed_chunks"] + int(resumed), active_frames=0)
                print(f"  {'RESUMED verified' if resumed else 'COMPLETE'}: "
                      f"{metadata['frame_count']} frames; {metadata['detection_samples']} detector samples; "
                      f"{time.monotonic() - chunk_started:.1f}s wall", flush=True)
            if status["completed_frames"] != status["total_frames"]:
                raise RuntimeError("final frame total mismatch")
            report(state="complete", active_chunk=None, active_frames=0, finished_at=utc_now())
            print(f"COMPLETE: {status['completed_chunks']} chunks, {status['completed_frames']} frames, "
                  f"{status['resumed_chunks']} resumed; status={out_dir / 'status.json'}", flush=True)
            return 0
        except BaseException as error:
            report(state="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                   error=f"{type(error).__name__}: {error}", finished_at=utc_now())
            raise


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        chunks = make_plan(args)
        if args.dry_run:
            print(json.dumps({"fps": FPS, "total_chunks": len(chunks),
                              "total_frames": sum(chunk.expected_frames for chunk in chunks),
                              "chunks": [dict(asdict(chunk), source=str(chunk.source)) for chunk in chunks]},
                             indent=2))
            return 0
        return execute_analysis(args, chunks)
    except KeyboardInterrupt:
        print("INTERRUPTED: incomplete chunk will be retried on resume", file=sys.stderr, flush=True)
        return 130
    except Exception as error:
        print(f"FAILED: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
