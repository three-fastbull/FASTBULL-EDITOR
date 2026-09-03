#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
project_dir="$(cd -- "$script_dir/.." && pwd -P)"
runtime_dir="$project_dir/.runtime/hyperframes/chromium"
browser_path="$runtime_dir/chromium"

cd "$project_dir"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js 22 or newer is required."
  exit 1
fi

node_major="$(node -p 'Number(process.versions.node.split(".")[0])')"
if (( node_major < 22 )); then
  echo "Node.js 22 or newer is required; found $(node --version)."
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg is required. Run the OpenMontage setup first."
  exit 1
fi

if [[ ! -x node_modules/.bin/hyperframes ]] || \
   [[ ! -f node_modules/@sparticuz/chromium/bin/chromium.br ]]; then
  npm install \
    --ignore-scripts \
    --no-save \
    --package-lock=false \
    hyperframes@0.8.27 \
    @sparticuz/chromium@149.0.0
fi

mkdir -p "$runtime_dir"

if [[ ! -x "$browser_path" ]]; then
  node --input-type=module - \
    "$project_dir/node_modules/@sparticuz/chromium/bin/chromium.br" \
    "$browser_path" <<'NODE'
import { chmod } from "node:fs/promises";
import { createReadStream, createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { createBrotliDecompress } from "node:zlib";

const [source, destination] = process.argv.slice(2);
await pipeline(
  createReadStream(source),
  createBrotliDecompress(),
  createWriteStream(destination),
);
await chmod(destination, 0o700);
NODE
fi

if [[ ! -f "$runtime_dir/libGLESv2.so" ]]; then
  swiftshader_tar="$runtime_dir/swiftshader.tar"
  node --input-type=module - \
    "$project_dir/node_modules/@sparticuz/chromium/bin/swiftshader.tar.br" \
    "$swiftshader_tar" <<'NODE'
import { createReadStream, createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { createBrotliDecompress } from "node:zlib";

const [source, destination] = process.argv.slice(2);
await pipeline(
  createReadStream(source),
  createBrotliDecompress(),
  createWriteStream(destination),
);
NODE
  tar --no-same-owner -xf "$swiftshader_tar" -C "$runtime_dir"
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

node --input-type=module - "$project_dir/.env" "$browser_path" <<'NODE'
import { readFileSync, writeFileSync } from "node:fs";

const [envPath, browserPath] = process.argv.slice(2);
const updates = {
  HYPERFRAMES_BROWSER_PATH: browserPath,
  HYPERFRAMES_NO_UPDATE_CHECK: "1",
  HYPERFRAMES_NO_AUTO_INSTALL: "1",
  HYPERFRAMES_NO_TELEMETRY: "1",
  NPM_CONFIG_OFFLINE: "true",
};

let body = readFileSync(envPath, "utf8");
for (const [key, value] of Object.entries(updates)) {
  const line = `${key}=${value}`;
  const pattern = new RegExp(`^${key}=.*$`, "m");
  body = pattern.test(body) ? body.replace(pattern, line) : `${body.trimEnd()}\n${line}\n`;
}
writeFileSync(envPath, body, "utf8");
NODE

export HYPERFRAMES_BROWSER_PATH="$browser_path"
export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_NO_AUTO_INSTALL=1
export HYPERFRAMES_NO_TELEMETRY=1
export NPM_CONFIG_OFFLINE=true

./node_modules/.bin/hyperframes telemetry disable

echo "HyperFrames $(./node_modules/.bin/hyperframes --version) is ready."
echo "Browser: $($browser_path --version)"
echo "Configuration: $project_dir/.env"

