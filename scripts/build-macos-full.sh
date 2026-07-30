#!/usr/bin/env bash
set -euo pipefail

# Build an optional self-contained macOS app. This intentionally remains
# separate from the normal 13 MB desktop shell because it embeds roughly 2 GB
# of Python wheels and TinySD weights.
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"
resource_root="$repo_root/src-tauri/package-resources"
python_env="${REAL_RUNTIME_ENV:-$repo_root/.venv-real}"
model_snapshot="${TINYSD_SNAPSHOT:-}"

if [[ ! -x "$python_env/bin/python" ]]; then
  echo "Missing real runtime: run ./scripts/setup-real-runtime.sh first." >&2
  exit 1
fi
if [[ -z "$model_snapshot" ]]; then
  model_snapshot="$(find "${HF_HOME:-$HOME/.cache/huggingface}/hub/models--segmind--tiny-sd/snapshots" -mindepth 1 -maxdepth 1 -type d -print -quit 2>/dev/null || true)"
fi
if [[ -z "$model_snapshot" || ! -f "$model_snapshot/model_index.json" ]]; then
  echo "TinySD snapshot not found. Download it once or set TINYSD_SNAPSHOT=/path/to/snapshot." >&2
  exit 1
fi

rm -rf "$resource_root"
mkdir -p "$resource_root/models/segmind/tiny-sd"
rsync -aL --delete \
  --exclude 'bin/Activate*' \
  --exclude 'bin/activate*' \
  "$python_env/" "$resource_root/.venv-real/"
rsync -aL --delete "$model_snapshot/" "$resource_root/models/segmind/tiny-sd/"
if command -v xattr >/dev/null 2>&1; then
  xattr -rc "$resource_root" >/dev/null 2>&1 || true
fi
tar -czf "$resource_root/real-runtime.tar.gz" -C "$resource_root" .venv-real
tar -czf "$resource_root/tiny-sd-model.tar.gz" -C "$resource_root" models
rm -rf "$resource_root/.venv-real" "$resource_root/models"

full_config="$(mktemp -t live-diffusion-tauri-config).json"
trap 'rm -f "$full_config"' EXIT
node -e '
const fs = require("fs");
const config = JSON.parse(fs.readFileSync("src-tauri/tauri.conf.json", "utf8"));
config.bundle.resources = {
  ...(config.bundle.resources || {}),
  "package-resources/real-runtime.tar.gz": "real-runtime.tar.gz",
  "package-resources/tiny-sd-model.tar.gz": "tiny-sd-model.tar.gz"
};
fs.writeFileSync(process.argv[1], JSON.stringify(config));
' "$full_config"

npm run tauri build -- --bundles app --config "$full_config"
echo "Full app bundle created with Python runtime and TinySD weights." >&2
