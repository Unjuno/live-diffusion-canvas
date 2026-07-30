"""Long-horizon intervention experiment.

Collects one image per runtime update and writes a human-inspectable contact
sheet plus machine-readable metrics. Run against the mock or a real backend:

  RUNTIME_URL=http://127.0.0.1:8001 RUNTIME_KIND=mock \
    python scripts/long-horizon-intervention.py
  RUNTIME_URL=http://127.0.0.1:8000 RUNTIME_KIND=tinysd \
    python scripts/long-horizon-intervention.py

The experiment deliberately separates intervention pulses from normal Explore
updates. A pulse is momentary: the mask is sent for one request and then
cleared for the following requests.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import hashlib
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat

BASE = os.getenv("RUNTIME_URL", "http://127.0.0.1:8000")
KIND = os.getenv("RUNTIME_KIND", "tinysd")
MODEL_ID = os.getenv("MODEL_ID", "segmind/tiny-sd")
OUT = Path(os.getenv("EXPERIMENT_OUT", f"artifacts/long-horizon/{KIND}"))
OUT.mkdir(parents=True, exist_ok=True)
STEPS = int(os.getenv("EXPERIMENT_STEPS", "8"))
HORIZON = int(os.getenv("EXPERIMENT_HORIZON", "32"))


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def mock_svg_to_image(value: str) -> Image.Image:
    """Rasterize the mock's SVG semantics without adding a browser dependency."""
    accent = "f06b5d" if "f06b5d" in value else "7c5cff"
    tick = re.search(r"FASTAPI STATE (\d+)", value)
    prompt = re.search(r">([^<>]*)</text></svg>", value)
    image = Image.new("RGB", (900, 600), "#" + accent)
    draw = ImageDraw.Draw(image)
    draw.text((40, 80), f"FASTAPI STATE {tick.group(1) if tick else '?'}", fill="white")
    draw.text((40, 125), prompt.group(1) if prompt else "", fill="white")
    return image


def decode(value: str) -> Image.Image:
    if value.startswith("data:image/svg+xml"):
        return mock_svg_to_image(value)
    raw = base64.b64decode(value.split(",", 1)[1])
    return Image.open(io.BytesIO(raw)).convert("RGB")


def mean_luma(image: Image.Image) -> float:
    return ImageStat.Stat(image.convert("L")).mean[0]


def mean_diff(left: Image.Image, right: Image.Image, box=None) -> float:
    if box:
        left, right = left.crop(box), right.crop(box)
    return sum(ImageStat.Stat(ImageChops.difference(left, right)).mean) / 3


def request(session: str, request_id: int, *, brush=False, guide=None, prompt=None) -> dict:
    return post("/runtime/intervention", {
        "requestId": request_id,
        "sessionId": session,
        "prompt": prompt or "a warm cabin beside a quiet lake",
        "guideComposite": guide,
        "guideInfluence": 1 if guide else 0.5,
        "globalExplorationNoiseStrength": 0.04,
        "temperature": float(os.getenv("EXPERIMENT_TEMPERATURE", "0.7")),
        "noiseBrushActive": brush,
        "activeNoiseMask": json.dumps([[45, 45], [50, 50], [55, 55]]) if brush else None,
        "localRejectionStrength": 0.9,
        "updatesToAdvance": 1,
        "phase": "explore",
        "diffusionSteps": STEPS,
    })


def image_data_url(path: str) -> str:
    raw = Path(path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def collect() -> tuple[list[Image.Image], list[dict]]:
    session = post("/runtime/session", {"seed": 913, "model": MODEL_ID if KIND != "mock" else None})["sessionId"]
    guide = None
    guide_image = os.getenv("GUIDE_IMAGE")
    frames, records = [], []
    for index in range(HORIZON):
        brush = index in {12, 25}
        if index == 18:
            guide = image_data_url(guide_image) if guide_image else "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpolyline%20points%3D%2220%2C20%2080%2C80%22%2F%3E%3C%2Fsvg%3E"
        response = request(session, index + 1, brush=brush, guide=guide)
        image = decode(response["previewImage"])
        image.save(OUT / f"frame-{index:03d}.png")
        frames.append(image)
        records.append({
            "index": index,
            "requestId": response["requestId"],
            "diffusionStep": response["diffusionStep"],
            "diffusionSteps": response["diffusionSteps"],
            "brush": brush,
            "luma": round(mean_luma(image), 3),
            "frameDifference": round(mean_diff(frames[-2], image), 3) if len(frames) > 1 else 0,
            "brushRegionDifference": round(mean_diff(frames[-2], image, (180, 180, 540, 540)), 3) if brush and len(frames) > 1 else None,
        })
    return frames, records


def main() -> None:
    frames, records = collect()
    tile_w, tile_h = 192, 144
    columns = 4
    sheet = Image.new("RGB", (columns * tile_w, ((len(frames) + columns - 1) // columns) * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        tile = frame.copy()
        tile.thumbnail((tile_w, tile_h))
        x, y = (index % columns) * tile_w, (index // columns) * tile_h
        sheet.paste(tile, (x, y))
        draw.text((x + 5, y + 5), f"{index:03d} s={records[index]['diffusionStep']}", fill="white")
    sheet.save(OUT / "contact-sheet.png")

    lumas = [record["luma"] for record in records]
    diffs = [record["frameDifference"] for record in records[1:]]
    brush_records = [record for record in records if record["brush"]]
    clipped = []
    saturated = []
    for image in frames:
        pixels = list(image.getdata())
        clipped.append(sum(1 for pixel in pixels if max(pixel) > 250 or min(pixel) < 5) / len(pixels))
        saturated.append(sum(1 for pixel in pixels if max(pixel) - min(pixel) > 100) / len(pixels))
    report = {
        "kind": KIND,
        "horizon": HORIZON,
        "frames": len(frames),
        "uniqueFrameHashes": len({hashlib.sha256(image.tobytes()).hexdigest() for image in frames}),
        "minLuma": round(min(lumas), 3),
        "maxLuma": round(max(lumas), 3),
        "maxClippedRatio": round(max(clipped), 5),
        "baselineClippedRatio": round(clipped[0], 5),
        "clippedRatioDelta": round(max(clipped[1:]) - clipped[0], 5) if len(clipped) > 1 else 0,
        "maxSaturatedRatio": round(max(saturated), 5),
        "meanFrameDifference": round(sum(diffs) / len(diffs), 3) if diffs else 0,
        "maxFrameDifference": round(max(diffs), 3) if diffs else 0,
        "brushEvents": brush_records,
        "stepSequence": [record["diffusionStep"] for record in records],
        "longHorizonBlack": min(lumas) < 8,
        "longHorizonClipping": (max(clipped[1:]) - clipped[0]) > 0.15 if len(clipped) > 1 else False,
        "stalled": sum(value > 0 for value in diffs) < max(3, HORIZON // 5),
    }
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["longHorizonBlack"] or report["longHorizonClipping"] or report["stalled"]:
        raise AssertionError(f"long-horizon intervention regression: {report}")


if __name__ == "__main__":
    main()
