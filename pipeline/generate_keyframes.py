"""Generate storyboard keyframes with Cloudflare Workers AI.

Load CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN from the environment
(for example, by sourcing the local .env file). Existing keyframes are skipped
unless --overwrite is supplied.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_PATH = ROOT / "storyboard.json"
LOG_PATH = ROOT / "runs.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "keyframes"


def append_log(record: dict) -> None:
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_image(url: str, token: str, prompt: str) -> tuple[bytes, int]:
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.loads(response.read().decode("utf-8"))
    latency_ms = round((time.perf_counter() - started) * 1000)
    image_b64 = result.get("result", {}).get("image")
    if not image_b64:
        raise RuntimeError("Cloudflare returned no result.image field")
    return base64.b64decode(image_b64), latency_ms


def describe_error(error: Exception) -> tuple[int | None, str]:
    if isinstance(error, urllib.error.HTTPError):
        return error.code, error.read().decode("utf-8", errors="replace")[:1200]
    if isinstance(error, urllib.error.URLError):
        return None, str(error.reason)
    return None, str(error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Cloudflare keyframes from storyboard.json.")
    parser.add_argument("--shot", help="Generate only this shot ID first, e.g. shot_01")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate keyframes that already exist")
    args = parser.parse_args()

    required = ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        print("Load them from your local .env file; never commit or share that file.", file=sys.stderr)
        return 2

    try:
        storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read valid storyboard.json: {error}", file=sys.stderr)
        return 1

    shots = storyboard.get("shots", [])
    if args.shot:
        shots = [shot for shot in shots if shot.get("id") == args.shot]
        if not shots:
            print(f"No storyboard shot found with ID {args.shot!r}.", file=sys.stderr)
            return 2

    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    model = os.environ.get("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for shot in shots:
        shot_id = shot["id"]
        output_path = OUTPUT_DIR / f"{shot_id}.jpg"
        if output_path.exists() and not args.overwrite:
            print(f"Skipping {shot_id}; {output_path.relative_to(ROOT)} already exists.")
            continue

        prompt = f"{storyboard['style']}\n\nShot: {shot['image_prompt']}"
        started = time.perf_counter()
        try:
            image_bytes, latency_ms = generate_image(url, token, prompt)
            output_path.write_bytes(image_bytes)
            append_log({
                "stage": "keyframe",
                "provider": "cloudflare_workers_ai",
                "model": model,
                "shot_id": shot_id,
                "parameters": {"prompt": prompt},
                "seed": None,
                "latency_ms": latency_ms,
                "cost_usd": None,
                "cost_note": "Check Workers AI usage in the Cloudflare dashboard.",
                "status": "success",
                "output": str(output_path.relative_to(ROOT)),
            })
            print(f"Generated {shot_id} ({latency_ms} ms): {output_path.relative_to(ROOT)}")
        except Exception as error:
            latency_ms = round((time.perf_counter() - started) * 1000)
            http_status, detail = describe_error(error)
            append_log({
                "stage": "keyframe",
                "provider": "cloudflare_workers_ai",
                "model": model,
                "shot_id": shot_id,
                "parameters": {"prompt": prompt},
                "seed": None,
                "latency_ms": latency_ms,
                "cost_usd": None,
                "status": "error",
                "http_status": http_status,
                "error_type": type(error).__name__,
                "error_detail": detail,
            })
            print(f"Keyframe {shot_id} failed (HTTP {http_status or 'n/a'}): {detail}", file=sys.stderr)
            return 1

    print(f"Keyframes are in {OUTPUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
