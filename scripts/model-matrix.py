"""Run the same midstream intervention regression for every ready model.

The matrix is intentionally explicit about skipped candidates. A model that is
listed in the catalog but has incomplete weights is not reported as passing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = os.getenv("RUNTIME_URL", "http://127.0.0.1:8000")
OUT = Path(os.getenv("MODEL_MATRIX_OUT", "artifacts/model-matrix"))


def get_models() -> list[dict]:
    with urllib.request.urlopen(BASE + "/runtime/models", timeout=10) as response:
        return json.load(response)


def main() -> None:
    results = []
    for model in get_models():
        model_id = model["id"]
        result = {"model": model_id, "label": model["label"], "profile": model["profile"]}
        if not model["modelReady"] or model["profile"] not in {"sd15-compatible", "sdxl-compatible"}:
            result.update({"status": "skipped", "reason": "weights unavailable or profile not implemented"})
            results.append(result)
            continue
        destination = OUT / model_id.replace("/", "__")
        environment = os.environ | {
            "RUNTIME_URL": BASE,
            "RUNTIME_KIND": "tinysd",
            "MODEL_ID": model_id,
            "EXPERIMENT_OUT": str(destination),
        }
        completed = subprocess.run(
            [sys.executable, "scripts/regression-midstream-intervention.py"],
            env=environment,
            check=False,
        )
        result.update({"status": "passed" if completed.returncode == 0 else "failed", "exitCode": completed.returncode, "output": str(destination)})
        results.append(result)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "matrix.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if any(result["status"] == "failed" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
