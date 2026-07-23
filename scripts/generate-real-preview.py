from __future__ import annotations

import argparse
import base64
from pathlib import Path

from backend.diffusion_runtime import TinySDRuntime

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", default="a quiet architectural landscape at blue hour")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--output", type=Path, default=Path("artifacts/tiny-sd-preview.png"))
args = parser.parse_args()

data_url, latency_ms = TinySDRuntime().generate(args.prompt, args.seed)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
print(f"wrote {args.output} ({latency_ms}ms)")
