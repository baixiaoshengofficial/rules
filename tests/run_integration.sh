#!/bin/sh
# Linux Docker integration test; never uses a real subscription.
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mihomo_bin=${MIHOMO_BIN:-mihomo}
test_image=${SUBCONVERTER_IMAGE:-tindy2013/subconverter@sha256:9fd004f00e90a7f67631f4d9a3f435c95b0fe58e7afdce8b8c6ca28c92826632}
command -v "$mihomo_bin" >/dev/null
docker image inspect "$test_image" >/dev/null
test_dir=$(mktemp -d)
container_name=rules-integration-$$

cleanup() {
  docker rm -f "$container_name" >/dev/null 2>&1 || true
  rm -rf "$test_dir"
}
trap cleanup EXIT HUP INT TERM

converter_port=$(python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)
docker run --rm --entrypoint sh "$test_image" -c 'cat pref.example.ini' \
  > "$test_dir/pref.ini"
sed -i "s/^listen=.*/listen=127.0.0.1/; s/^port=.*/port=$converter_port/; s/^async_fetch_ruleset=.*/async_fetch_ruleset=true/" \
  "$test_dir/pref.ini"
docker run -d --rm --network host --name "$container_name" \
  -v "$test_dir/pref.ini:/base/pref.ini:ro" "$test_image" >/dev/null
python3 - "$converter_port" <<'PY'
import sys
import time
import urllib.request
for attempt in range(100):
    try:
        with urllib.request.urlopen("http://127.0.0.1:" + sys.argv[1] + "/version", timeout=1):
            break
    except OSError:
        time.sleep(0.1)
else:
    raise SystemExit("Subconverter did not start")
PY
python3 "$repo_dir/tests/test_integration.py" --mihomo "$mihomo_bin" \
  --subconverter-url "http://127.0.0.1:$converter_port" "$@"
