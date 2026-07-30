"""Verify interventions while Explore is still advancing, not after Finish.

The sequence intentionally changes the guide at an unfinished timestep and
holds Noise Brush on a later update. It records every response and asserts
that the same session continues, images change, and no dark/stalled frame is
produced.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import urllib.request
from urllib.parse import unquote
from pathlib import Path

from PIL import Image, ImageChops, ImageStat, ImageDraw

BASE = os.getenv("RUNTIME_URL", "http://127.0.0.1:8000")
KIND = os.getenv("RUNTIME_KIND", "mock")
MODEL_ID = os.getenv("MODEL_ID", "segmind/tiny-sd")
OUT = Path(os.getenv("EXPERIMENT_OUT", f"artifacts/midstream/{KIND}"))
OUT.mkdir(parents=True, exist_ok=True)


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def decode(value: str) -> Image.Image:
    if value.startswith("data:image/svg+xml"):
        decoded = unquote(value.split(",", 1)[1])
        tick = re.search(r"FASTAPI STATE (\d+)", decoded)
        accent = "#f06b5d" if "#f06b5d" in decoded or "%23f06b5d" in value else "#7c5cff"
        image = Image.new("RGB", (900, 600), accent)
        ImageDraw.Draw(image).text((40, 80), f"FASTAPI STATE {tick.group(1) if tick else '?'}", fill="white")
        return image
    return Image.open(io.BytesIO(base64.b64decode(value.split(",", 1)[1]))).convert("RGB")


def diff(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def main() -> None:
    session = post("/runtime/session", {"seed": 2407, "model": MODEL_ID if KIND != "mock" else None})["sessionId"]
    guide = None
    frames: list[Image.Image] = []
    records: list[dict] = []
    for request_id in range(1, 17):
        if request_id == 5:
            guide = "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpolyline%20points%3D%2220%2C80%2080%2C20%22%2F%3E%3C%2Fsvg%3E"
        brush = request_id == 9
        response = post("/runtime/intervention", {
            "requestId": request_id,
            "sessionId": session,
            "prompt": "a glasshouse beside a dark lake",
            "guideComposite": guide,
            "guideInfluence": 1 if guide else 0.5,
            "globalExplorationNoiseStrength": 0.04,
            "temperature": 0.8,
            "noiseBrushActive": brush,
            "activeNoiseMask": json.dumps([[44, 44], [50, 50], [56, 56]]) if brush else None,
            "localRejectionStrength": 0.9,
            "brushSize": 48,
            "updatesToAdvance": 1,
            "phase": "explore",
            "diffusionSteps": 8,
        })
        image = decode(response["previewImage"])
        image.save(OUT / f"frame-{request_id:02d}.png")
        frames.append(image)
        records.append({
            "requestId": request_id,
            "sessionId": response["sessionId"],
            "diffusionStep": response.get("diffusionStep", 0),
            "guideActive": guide is not None,
            "brushActive": brush,
            "frameDifference": round(diff(frames[-2], image), 3) if len(frames) > 1 else 0,
            "luma": round(ImageStat.Stat(image.convert("L")).mean[0], 3),
            "hash": hashlib.sha256(image.tobytes()).hexdigest(),
        })
    report = {
        "kind": KIND,
        "session": session,
        "frames": len(frames),
        "uniqueFrameHashes": len({record["hash"] for record in records}),
        "nonzeroFrameChanges": sum(record["frameDifference"] > 0.001 for record in records[1:]),
        "guideTransitionDifference": records[4]["frameDifference"],
        "brushTransitionDifference": records[8]["frameDifference"],
        "minLuma": min(record["luma"] for record in records),
        "stepSequence": [record["diffusionStep"] for record in records],
        "singleSession": all(record["sessionId"] == session for record in records),
        "records": records,
    }
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    sheet = Image.new("RGB", (640, 480), "white")
    for index, image in enumerate(frames):
        tile = image.copy(); tile.thumbnail((160, 120))
        sheet.paste(tile, ((index % 4) * 160, (index // 4) * 120))
    sheet.save(OUT / "contact-sheet.png")
    print(json.dumps(report, indent=2))
    assert report["singleSession"]
    assert report["uniqueFrameHashes"] > 4
    assert report["nonzeroFrameChanges"] >= 10
    assert report["guideTransitionDifference"] > 0.001
    assert report["brushTransitionDifference"] > 0.1
    assert report["minLuma"] > 8


if __name__ == "__main__":
    main()
