"""Generate and validate real-runtime regression images.

Run with the real model environment while backend.app is serving with
DIFFUSION_REAL=1. The saved contact sheet is intentionally inspectable: the
numeric assertions catch regressions, and the image remains the final judge.
"""

from __future__ import annotations

import base64
import io
import json
import os
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageStat, ImageDraw

BASE = os.getenv("RUNTIME_URL", "http://127.0.0.1:8000")
OUT = Path(os.getenv("REGRESSION_OUT", "artifacts/regression"))
OUT.mkdir(parents=True, exist_ok=True)


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def image(response: dict, name: str) -> Image.Image:
    raw = base64.b64decode(response["previewImage"].split(",", 1)[1])
    result = Image.open(io.BytesIO(raw)).convert("RGB")
    result.save(OUT / f"{name}.png")
    return result


def mean_luma(value: Image.Image) -> float:
    return sum(ImageStat.Stat(value.convert("L")).mean) / 1


def mean_difference(left: Image.Image, right: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(left, right)).mean) / 3


def session(seed: int) -> str:
    return post("/runtime/session", {"seed": seed})["sessionId"]


def request(session_id: str, request_id: int, **extra: object) -> dict:
    payload = {
        "requestId": request_id,
        "sessionId": session_id,
        "prompt": "a warm cabin beside a quiet lake",
        "diffusionSteps": 8,
        "updatesToAdvance": 1,
        "phase": "explore",
        **extra,
    }
    return post("/runtime/intervention", payload)


def finish_explore(session_id: str, start_request: int, **extra: object) -> dict:
    response = None
    for request_id in range(start_request, start_request + 12):
        response = request(session_id, request_id, **extra)
        if response["diffusionStep"] == response["diffusionSteps"]:
            return response
    raise AssertionError("runtime did not reach the terminal diffusion step")


def main() -> None:
    baseline = image(finish_explore(session(1200), 1), "01-baseline")
    prompt = image(finish_explore(session(1200), 1, prompt="a red spaceship above an alien ocean"), "02-prompt")
    guide_svg = (
        "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20"
        "width%3D%22512%22%20height%3D%22512%22%3E%3Cpolyline%20points%3D%2220%2C20%2080%2C80%22%2F%3E%3C%2Fsvg%3E"
    )
    guide = image(finish_explore(session(1200), 1, guideComposite=guide_svg, guideInfluence=1), "03-guide")

    brush_session = session(1201)
    current = None
    for index in range(1, 5):
        current = request(brush_session, index)
    before_brush = image(finish_explore(brush_session, 5), "04-before-brush")
    brushed = image(
        request(
            brush_session,
            5,
            noiseBrushActive=True,
            activeNoiseMask=json.dumps([[45, 45], [50, 50], [55, 55]]),
            localRejectionStrength=0.9,
        ),
        "05-brush",
    )

    continued = finish_explore(brush_session, 6)
    after_complete = image(continued, "06-continued")

    checks = {
        "prompt_difference": round(mean_difference(baseline, prompt), 3),
        "guide_difference": round(mean_difference(baseline, guide), 3),
        "brush_difference": round(mean_difference(before_brush, brushed), 3),
        "continued_difference": round(mean_difference(brushed, after_complete), 3),
        "minimum_luma": round(min(mean_luma(x) for x in [baseline, prompt, guide, before_brush, brushed, after_complete]), 3),
        "continued_step": continued["diffusionStep"],
    }
    if checks["prompt_difference"] <= 0.1 or checks["guide_difference"] <= 0.05 or checks["brush_difference"] <= 0.1:
        raise AssertionError(f"interaction regression: {checks}")
    if checks["minimum_luma"] < 8 or checks["continued_step"] <= 0:
        raise AssertionError(f"dark/stalled regression: {checks}")

    tiles = [Image.open(OUT / f"0{i}-{name}.png").resize((256, 192)) for i, name in enumerate(["baseline", "prompt", "guide", "before-brush", "brush", "continued"], 1)]
    sheet = Image.new("RGB", (768, 384), "white")
    draw = ImageDraw.Draw(sheet)
    for index, tile in enumerate(tiles):
        x, y = (index % 3) * 256, (index // 3) * 192
        sheet.paste(tile, (x, y))
        draw.text((x + 8, y + 8), str(index + 1), fill="white")
    sheet.save(OUT / "00-contact-sheet.png")
    (OUT / "metrics.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
