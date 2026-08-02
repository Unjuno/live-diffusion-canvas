#!/usr/bin/env python3
"""Download a catalogued model without tying work to an HTTP request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


CATALOG = {
    "segmind/tiny-sd",
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    "stabilityai/sd-turbo",
    "stabilityai/sdxl-turbo",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-3.5-medium",
}


def patterns_for(model: str) -> list[str] | None:
    """Keep snapshots small and aligned with the runtime's load contract."""
    if model == "stabilityai/sd-turbo":
        return [
            "model_index.json", "scheduler/**", "tokenizer/**", "text_encoder/config.json",
            "text_encoder/model.fp16.safetensors", "unet/config.json",
            "unet/diffusion_pytorch_model.fp16.safetensors", "vae/config.json",
            "vae/diffusion_pytorch_model.fp16.safetensors",
        ]
    if model in {"stabilityai/sdxl-turbo", "stabilityai/stable-diffusion-xl-base-1.0"}:
        return [
            "model_index.json", "scheduler/**", "tokenizer/**", "tokenizer_2/**",
            "text_encoder/**", "text_encoder_2/**", "unet/config.json",
            "unet/diffusion_pytorch_model.fp16.safetensors", "vae/config.json",
            "vae/diffusion_pytorch_model.fp16.safetensors",
        ]
    if model == "black-forest-labs/FLUX.1-schnell":
        return [
            "model_index.json", "scheduler/**", "transformer/**", "vae/**",
            "tokenizer/**", "tokenizer_2/**", "text_encoder/**", "text_encoder_2/**",
        ]
    if model == "stabilityai/stable-diffusion-3.5-medium":
        return [
            "model_index.json", "scheduler/**", "transformer/**", "vae/**",
            "tokenizer/**", "tokenizer_2/**", "tokenizer_3/**", "text_encoder/**",
            "text_encoder_2/**", "text_encoder_3/**",
        ]
    return None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(path: Path, **values: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = {}
    if path.exists():
        try:
            current = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            current = {}
    current.update(values, updatedAt=now())
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(current, indent=2) + "\n")
    temporary.replace(path)


def _hf_cache_root() -> Path:
    return Path(os.getenv("HF_HOME", Path.home() / ".cache/huggingface")) / "hub"


def _download_large_sd_turbo_files() -> None:
    """Use resumable range downloads for the two large SD-Turbo blobs."""
    cache = _hf_cache_root() / "models--stabilityai--sd-turbo"
    blobs = cache / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    files = (
        ("text_encoder/model.fp16.safetensors", "bc1827c465450322616f06dea41596eac7d493f4e95904dcb51f0fc745c4e13f", 680820392),
        ("unet/diffusion_pytorch_model.fp16.safetensors", "40ec400881e27d1376c7c95c5bd495f407b33756e80eb6365e301c33a07af6e5", 1731904736),
    )
    for relative, digest, expected_size in files:
        target = blobs / digest
        if target.exists() and target.stat().st_size == expected_size:
            continue
        partials = list(blobs.glob(digest + ".*.incomplete"))
        partial = max(partials, key=lambda path: path.stat().st_size) if partials else blobs / (digest + ".download.incomplete")
        url = "https://huggingface.co/stabilityai/sd-turbo/resolve/main/" + relative
        for attempt in range(2):
            command = ["curl", "-L", "--fail", "--retry", "8", "--retry-all-errors"]
            if attempt == 0:
                command.extend(["-C", "-"])
            command.extend(["-o", str(partial), url])
            subprocess.run(command, check=True)
            if partial.stat().st_size != expected_size:
                if attempt == 0:
                    partial.unlink(missing_ok=True)
                    continue
                raise RuntimeError(f"Incomplete download for {relative}: {partial.stat().st_size}/{expected_size}")
            checksum = hashlib.sha256()
            with partial.open("rb") as stream:
                for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    checksum.update(chunk)
            digest_actual = checksum.hexdigest()
            if digest_actual == digest:
                break
            if attempt == 0:
                partial.unlink(missing_ok=True)
        else:
            raise RuntimeError(f"Checksum mismatch for {relative}: {digest_actual}")
        partial.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--status-dir", required=True, type=Path)
    parser.add_argument("--revision", default="main")
    args = parser.parse_args()
    if args.model not in CATALOG:
        raise SystemExit(f"Model is not in the catalog: {args.model}")
    status_path = args.status_dir / (args.model.replace("/", "__") + ".json")
    write_status(status_path, model=args.model, status="downloading", pid=os.getpid(), startedAt=now(), error=None)
    try:
        from huggingface_hub import snapshot_download

        if args.model == "stabilityai/sd-turbo":
            _download_large_sd_turbo_files()

        snapshot = snapshot_download(
            repo_id=args.model,
            revision=args.revision,
            max_workers=4,
            allow_patterns=patterns_for(args.model),
        )
        write_status(status_path, model=args.model, status="ready", snapshotPath=snapshot, error=None)
        return 0
    except Exception as error:  # status is consumed by the UI and remains resumable
        write_status(status_path, model=args.model, status="error", error=f"{type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
