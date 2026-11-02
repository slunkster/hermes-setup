// Measure the bright content rect of a device screenshot and its aspect ratio.
// Proves a camera viewfinder or a target frame actually matches the saved photo's
// aspect, instead of "looks about right" in a screenshot review.
//
//   swift measure-frame-aspect.swift shot.png [expectedRatio]
//
// Exit codes: 0 measured (and matched, when an expected ratio is given), 1 mismatch,
// 2 bad usage. Scan lines deliberately avoid the centre column so on-screen controls
// and centre overlays do not pollute the measurement.

import Foundation
import CoreGraphics
import ImageIO

let args = CommandLine.arguments

guard args.count >= 2 else {
    print("usage: measure-frame-aspect.swift <screenshot.png> [expectedRatio]")
    exit(2)
}

let path = args[1]
let expected = args.count >= 3 ? Double(args[2]) : nil

func loadPixels(_ path: String) -> (w: Int, h: Int, data: [UInt8])? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { return nil }
    let w = img.width, h = img.height
    var data = [UInt8](repeating: 0, count: w * h * 4)
    guard let ctx = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8,
                              bytesPerRow: w * 4, space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
    ctx.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
    return (w, h, data)
}

func run() {
    guard let image = loadPixels(path) else {
        print("cannot read \(path)")
        exit(1)
    }
    let (w, h, data) = image
    let threshold = 12

    func lum(_ x: Int, _ y: Int) -> Int {
        let i = ((h - 1 - y) * w + x) * 4
        return (Int(data[i]) + Int(data[i + 1]) + Int(data[i + 2])) / 3
    }

    func rowExtent(_ y: Int) -> (Int, Int) {
        var left = -1, right = -1
        for x in 0..<w where lum(x, y) > threshold { left = x; break }
        for x in stride(from: w - 1, through: 0, by: -1) where lum(x, y) > threshold { right = x; break }
        return (left, right)
    }

    func colExtent(_ x: Int) -> (Int, Int) {
        var top = -1, bottom = -1
        for y in 0..<h where lum(x, y) > threshold { top = y; break }
        for y in stride(from: h - 1, through: 0, by: -1) where lum(x, y) > threshold { bottom = y; break }
        return (top, bottom)
    }

    let (left, right) = rowExtent(Int(Double(h) * 0.45))
    let probeColumn = min(w - 1, w / 2 + 200)
    let (top, bottom) = colExtent(probeColumn)

    guard left >= 0, right > left, top >= 0, bottom > top else {
        print("no content found — is the panel black or the screenshot empty?")
        exit(1)
    }

    let cw = right - left + 1
    let ch = bottom - top + 1
    let ratio = Double(cw) / Double(ch)

    print("image \(w)x\(h)")
    print("content x=\(left)..\(right) y=\(top)..\(bottom) size=\(cw)x\(ch)")
    print(String(format: "ratio %.4f", ratio))

    if let expected {
        let ok = abs(ratio - expected) < 0.01
        print(String(format: "expected %.4f -> %@", expected, ok ? "MATCH" : "MISMATCH"))
        exit(ok ? 0 : 1)
    }
}

run()
