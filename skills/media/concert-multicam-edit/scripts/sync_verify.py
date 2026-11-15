"""Read-only concert audio sync verification; stdlib + numpy, no scipy.

Offset convention: B_global = A_global - offset_seconds. A/B globals are
seconds along their own two concatenated files, NOT the local file timestamp.
A windows START at the requested times. A 60s window is compared against a
64s B buffer centered on the prior 21.04s offset, at 10ms resolution.
"""
import argparse
import datetime
import json
from pathlib import Path
import subprocess

import numpy as np


EXPECTED_OFFSET = 21.04
SEARCH_RADIUS = 2.0
ENVELOPE_HZ = 100


def correlate_envelopes(a, b, a_start, expected=EXPECTED_OFFSET,
                        radius=SEARCH_RADIUS, hz=ENVELOPE_HZ):
    """NCC of fixed A against shifted B; B starts Astart-expected-radius."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    steps = int(round(2 * radius * hz))
    if a.ndim != 1 or b.ndim != 1 or len(a) < 3 or len(b) != len(a) + steps:
        raise ValueError("Expected 1-D A and B=A+2*radius*hz envelope bins")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Non-finite envelopes")
    centered = a - a.mean()
    # Offset centering prevents cancellation in rolling variance.
    shifted = b - b.mean()
    sums = np.concatenate(([0.0], np.cumsum(shifted)))
    squares = np.concatenate(([0.0], np.cumsum(shifted * shifted)))
    n = len(a)
    variance = np.maximum(0.0, squares[n:] - squares[:-n]
                          - (sums[n:] - sums[:-n]) ** 2 / n)
    denom = np.sqrt(np.dot(centered, centered) * variance)
    scores = np.divide(np.correlate(shifted, centered, mode="valid"), denom,
                       out=np.zeros_like(denom), where=denom > 1e-12)
    scores = np.clip(scores, -1.0, 1.0)
    best = int(np.argmax(scores))
    exclusion = max(1, int(round(0.15 * hz)))
    competitors = np.abs(np.arange(len(scores)) - best) > exclusion
    second = float(np.max(scores[competitors])) if competitors.any() else -1.0
    reasons = []
    if float(np.std(a)) < 1e-4 or float(np.std(b)) < 1e-4:
        reasons.append("flat_or_silent_envelope")
    if scores[best] < 0.20:
        reasons.append("low_correlation")
    if scores[best] - second < 0.04:
        reasons.append("ambiguous_peak")
    if best == 0 or best == steps:
        reasons.append("peak_at_search_boundary")
    # Ranked local maxima, with nonmaximum suppression at 150ms.
    local = [i for i in range(len(scores))
             if (i == 0 or scores[i] >= scores[i - 1])
             and (i == steps or scores[i] >= scores[i + 1])]
    selected = []
    for i in sorted(local, key=lambda k: float(scores[k]), reverse=True):
        if all(abs(i - j) > exclusion for j in selected):
            selected.append(i)
        if len(selected) == 5:
            break
    offset = float(expected + radius - best / hz)
    return {"a_start_seconds": float(a_start), "a_center_seconds": float(a_start + n / hz / 2),
            "b_buffer_start_seconds": float(a_start - expected - radius),
            "offset_seconds": offset, "b_time_seconds": float(a_start - offset),
            "peak_correlation": float(scores[best]), "competing_correlation": second,
            "peak_margin": float(scores[best] - second), "accepted": not reasons,
            "warnings": reasons,
            "peaks": [{"offset_seconds": float(expected + radius - i / hz),
                       "correlation": float(scores[i])} for i in selected]}


def summarize(windows, expected=EXPECTED_OFFSET, tolerance=0.04):
    """Conservative gate for retaining the *existing constant* camera offset.

    A measured offset differing from the prior is NOT automatically applied.
    Drift is d(offset)/d(A time); positive means B runs increasingly behind A.
    """
    accepted = [w for w in windows if w.get("accepted", False)]
    result = {"status": "warning", "accepted_windows": len(accepted),
              "total_windows": len(windows), "consensus_offset_seconds": None,
              "offset_at_A_zero_seconds": None, "drift_ppm": None,
              "drift_seconds_per_hour": None, "drift_over_test_span_seconds": None,
              "max_fit_residual_seconds": None, "tolerance_seconds": tolerance,
              "warnings": []}
    warnings = result["warnings"]
    if len(accepted) != len(windows):
        warnings.append("one_or_more_windows_unreliable")
    if len(accepted) < 3:
        warnings.append("insufficient_reliable_windows")
        return result
    times = np.array([w["a_center_seconds"] for w in accepted], dtype=float)
    offsets = np.array([w["offset_seconds"] for w in accepted], dtype=float)
    if np.ptp(times) <= 0:
        warnings.append("insufficient_time_span")
        return result
    tc = times - times.mean()
    slope = float(np.dot(tc, offsets - offsets.mean()) / np.dot(tc, tc))
    intercept = float(offsets.mean() - slope * times.mean())
    residual = float(np.max(np.abs(offsets - (intercept + slope * times))))
    drift = float(slope * np.ptp(times))
    consensus = float(np.median(offsets))
    result.update(consensus_offset_seconds=consensus,
                  offset_at_A_zero_seconds=intercept,
                  drift_ppm=slope * 1e6, drift_seconds_per_hour=slope * 3600,
                  drift_over_test_span_seconds=drift,
                  max_fit_residual_seconds=residual,
                  measured_offset_range_seconds=[float(offsets.min()), float(offsets.max())])
    if abs(drift) > tolerance + 1e-9:
        warnings.append("constant_offset_drift_exceeds_tolerance")
    if residual > tolerance + 1e-9:
        warnings.append("offsets_disagree_with_linear_drift")
    if np.max(np.abs(offsets - expected)) > tolerance + 1e-9:
        warnings.append("prior_offset_not_valid_at_all_windows")
    result["status"] = "warning" if warnings else "pass"
    return result


SAMPLE_RATE = 8000
WINDOW_TIMES = (1000, 6000, 10000, 14000, 17000)
WINDOW_SECONDS = 60.0


def decode_pcm(sources, start, duration, ffmpeg):
    """Read a global interval from sequential (path, duration) sources.

    All boundaries are rounded once to 8kHz sample indices. No silence padding,
    dropped chunks, intermediate media, shell invocation or source writes.
    """
    first = int(round(start * SAMPLE_RATE))
    count = int(round(duration * SAMPLE_RATE))
    lengths = [int(round(seconds * SAMPLE_RATE)) for _, seconds in sources]
    if first < 0 or count <= 0 or first + count > sum(lengths):
        raise ValueError(f"Global interval [{start}, {start + duration}) outside source coverage")
    chunks = []
    source_start = 0
    for (path, _), length in zip(sources, lengths):
        lo = max(first, source_start)
        hi = min(first + count, source_start + length)
        if hi > lo:
            local = (lo - source_start) / SAMPLE_RATE
            seconds = (hi - lo) / SAMPLE_RATE
            command = [str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "error",
                       "-ss", f"{local:.9f}", "-i", str(path), "-t", f"{seconds:.9f}",
                       "-map", "0:a:0", "-vn", "-sn", "-dn", "-ac", "1", "-ar", str(SAMPLE_RATE),
                       "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"]
            try:
                process = subprocess.run(command, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, timeout=180, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"ffmpeg timed out for {path} at {local:.3f}s") from exc
            if process.returncode:
                error = process.stderr.decode("utf-8", errors="replace")[-2000:]
                raise RuntimeError(f"ffmpeg failed for {path}: {error}")
            if len(process.stdout) != (hi - lo) * 4:
                raise RuntimeError(f"Decoded sample count mismatch for {path}: "
                                   f"expected {hi - lo}, got {len(process.stdout) / 4:g}")
            pcm = np.frombuffer(process.stdout, dtype="<f4")
            if not np.isfinite(pcm).all():
                raise RuntimeError(f"Non-finite PCM from {path}")
            chunks.append(pcm)
        source_start += length
    return np.concatenate(chunks)


def log_rms(pcm):
    """Natural-log RMS for nonoverlapping 80-sample (10ms) bins."""
    pcm = np.asarray(pcm, dtype=np.float64)
    if pcm.ndim != 1 or not len(pcm) or len(pcm) % 80:
        raise ValueError("PCM must contain an exact number of 10ms mono bins")
    if not np.isfinite(pcm).all():
        raise ValueError("Non-finite PCM")
    return np.log(np.maximum(np.sqrt(np.mean(pcm.reshape(-1, 80) ** 2, axis=1)), 1e-10))


def verify(a_sources, b_sources, ffmpeg, decoder=None):
    """Analyze all five windows, preserving failures as unaccepted records."""
    decoder = decode_pcm if decoder is None else decoder
    windows = []
    for start in WINDOW_TIMES:
        try:
            a = decoder(a_sources, start, WINDOW_SECONDS, ffmpeg)
            b = decoder(b_sources, start - EXPECTED_OFFSET - SEARCH_RADIUS,
                        WINDOW_SECONDS + 2 * SEARCH_RADIUS, ffmpeg)
            if len(a) != int(WINDOW_SECONDS * SAMPLE_RATE) or len(b) != int(
                    (WINDOW_SECONDS + 2 * SEARCH_RADIUS) * SAMPLE_RATE):
                raise ValueError("Unexpected decoded sample count")
            windows.append(correlate_envelopes(log_rms(a), log_rms(b), start))
        except (OSError, ValueError, RuntimeError) as exc:
            windows.append({"a_start_seconds": float(start), "accepted": False,
                            "warnings": ["extraction_or_analysis_error"],
                            "error": str(exc), "peaks": []})
    return {"schema_version": 1,
            "offset_convention": "B_global_seconds = A_global_seconds - offset_seconds",
            "window_times_are": "A window start times",
            "expected_offset_seconds": EXPECTED_OFFSET,
            "search_radius_seconds": SEARCH_RADIUS, "window_seconds": WINDOW_SECONDS,
            "sample_rate_hz": SAMPLE_RATE, "envelope_bin_seconds": 0.01,
            "thresholds": {"minimum_correlation": 0.20, "minimum_peak_margin": 0.04,
                           "competing_peak_exclusion_seconds": 0.15,
                           "constant_offset_tolerance_seconds": 0.04},
            "windows": windows, "summary": summarize(windows)}


DEFAULT_BASE = "G:/Active Media/Blues Fest"
DEFAULT_FFMPEG = "C:/Users/Siim Alve/AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe"
SOURCE_SPECS = {
    "A": (("A089C001_260904_DJ0B.MOV", 11040.48),
          ("A089C002_260904_DJ0B.MOV", 7027.68)),
    "B": (("S1310001.MP4", 11040.96), ("S1310002.MP4", 6825.6)),
}


def resolve_sources(base):
    """Find unique exact source filenames recursively; reject missing/duplicates."""
    base = Path(base)
    if not base.is_dir():
        raise FileNotFoundError(f"Media base directory not found: {base}")
    resolved = {}
    for camera, specs in SOURCE_SPECS.items():
        resolved[camera] = []
        for name, duration in specs:
            matches = sorted(set(base.rglob(name)))
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one {name} under {base}; found {len(matches)}: "
                                 + ", ".join(str(p) for p in matches))
            resolved[camera].append((matches[0], duration))
    return resolved["A"], resolved["B"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path(DEFAULT_BASE),
                        help="Root containing the four unique camera files (recursive search)")
    parser.add_argument("--ffmpeg", type=Path, default=Path(DEFAULT_FFMPEG))
    args = parser.parse_args(argv)
    sources = {}
    try:
        if not args.ffmpeg.is_file():
            raise FileNotFoundError(f"ffmpeg executable not found: {args.ffmpeg}")
        a, b = resolve_sources(args.base)
        sources = {camera: [{"path": str(path), "duration_seconds": seconds}
                            for path, seconds in items]
                   for camera, items in (("A", a), ("B", b))}
        report = verify(a, b, args.ffmpeg)
    except (OSError, ValueError, RuntimeError) as exc:
        report = {"schema_version": 1, "windows": [], "summary": summarize([]), "error": str(exc)}
    report.update(generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  sources=sources, ffmpeg=str(args.ffmpeg), media_base=str(args.base),
                  source_durations_kind="user_supplied_contiguous_file_durations",
                  requested_a_window_start_seconds=list(WINDOW_TIMES))
    output = Path(__file__).resolve().with_suffix(".json")
    try:
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: cannot write verification JSON: {exc}")
        return 2
    summary = report["summary"]
    print(f"{summary['status'].upper()}: {output}")
    print(json.dumps(summary, indent=2, allow_nan=False))
    if "error" in report:
        print(report["error"])
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
