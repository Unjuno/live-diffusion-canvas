#!/usr/bin/env bash
set -euo pipefail

runtime_url="${RUNTIME_URL:-http://127.0.0.1:8000}"
model="${MODEL_ID:-segmind/tiny-sd}"
kind="${RUNTIME_KIND:-real}"
seed="${VERIFY_SEED:-811}"

health="$(curl --silent --show-error --fail --max-time 5 "$runtime_url/runtime/health?model=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$model")")"
echo "$health"
if [[ "$health" != *'"status":"ok"'* ]]; then
  echo "Runtime health is not ok" >&2
  exit 1
fi
if [[ "$kind" == "real" && "$health" != *'"runtime":"diffusers"'* ]]; then
  echo "Expected a real Diffusers runtime" >&2
  exit 1
fi
if [[ "$kind" == "real" && "$health" != *'"modelReady":true'* ]]; then
  echo "The requested model is not ready" >&2
  exit 1
fi

payload="$(MODEL_ID="$model" VERIFY_SEED="$seed" RUNTIME_KIND="$kind" python3 - "$runtime_url" <<'PY'
import base64, json, os, sys, urllib.request

base = sys.argv[1]
model = os.environ["MODEL_ID"] if os.environ["RUNTIME_KIND"] == "real" else None
def post(path, value):
    request = urllib.request.Request(base + path, data=json.dumps(value).encode(), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)

session = post("/runtime/session", {"seed": int(os.environ["VERIFY_SEED"]), "model": model})
result = post("/runtime/intervention", {
    "requestId": 1,
    "sessionId": session["sessionId"],
    "prompt": "a small red cabin beside a lake at dawn",
    "guideInfluence": 0.5,
    "globalExplorationNoiseStrength": 0.04,
    "temperature": 0.7,
    "noiseBrushActive": False,
    "localRejectionStrength": 0.7,
    "updatesToAdvance": 1,
    "phase": "explore",
    "diffusionSteps": 8,
})
image = result.get("previewImage", "")
if not image.startswith("data:image/"):
    raise SystemExit("Runtime did not return an image data URL")
if image.startswith("data:image/png;base64,") and len(base64.b64decode(image.split(",", 1)[1])) < 100:
    raise SystemExit("Runtime returned an unexpectedly small PNG")
print(json.dumps({"sessionId": session["sessionId"], "requestId": result.get("requestId"), "diffusionStep": result.get("diffusionStep"), "diffusionSteps": result.get("diffusionSteps"), "previewBytes": len(image)}))
PY
)"
echo "$payload"
