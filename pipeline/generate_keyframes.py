"""Generate storyboard keyframes with Cloudflare Workers AI.

Load Cloudflare credentials from the environment. Existing keyframes are
skipped unless --overwrite is supplied. FLUX.2 Klein is used for image
reference conditioning; FLUX.1 schnell remains available for text-only calls.
"""

from __future__ import annotations

import argparse
import base64
import io
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


def prepare_reference(path: Path) -> bytes:
    """Resize a reference image below 512x512, as required by FLUX.2 Klein."""
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required for reference images. Install requirements.txt first.") from error

    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((511, 511), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=88, optimize=True)
    return output.getvalue()


def build_multipart(prompt: str, reference_bytes: bytes | None) -> tuple[bytes, str]:
    """Build the multipart REST request accepted by FLUX.2 Klein."""
    boundary = f"----heritage-short-{os.urandom(12).hex()}"
    parts = [
        f"--{boundary}\r\n".encode("ascii"),
        b'Content-Disposition: form-data; name="prompt"\r\n\r\n',
        prompt.encode("utf-8"),
        b"\r\n",
    ]
    if reference_bytes is not None:
        parts.extend([
            f"--{boundary}\r\n".encode("ascii"),
            b'Content-Disposition: form-data; name="input_image_0"; filename="family_style_reference.jpg"\r\n',
            b"Content-Type: image/jpeg\r\n\r\n",
            reference_bytes,
            b"\r\n",
        ])
    parts.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def generate_image(
    url: str,
    token: str,
    model: str,
    prompt: str,
    reference_bytes: bytes | None = None,
) -> tuple[bytes, int]:
    if reference_bytes is not None and "flux-2-klein" not in model:
        raise ValueError("Reference images require a FLUX.2 Klein model.")

    if "flux-2-klein" in model:
        payload, content_type = build_multipart(prompt, reference_bytes)
    else:
        payload = json.dumps({"prompt": prompt}).encode("utf-8")
        content_type = "application/json"

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
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
    parser.add_argument("--shot", help="Generate only this shot ID first, e.g. shot_02")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate keyframes that already exist")
    parser.add_argument("--reference", metavar="PATH", help="Family/style reference image (requires FLUX.2 Klein)")
    parser.add_argument("--model", help="Workers AI model ID; use @cf/black-forest-labs/flux-2-klein-4b with --reference")
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

    default_model = "@cf/black-forest-labs/flux-2-klein-4b" if args.reference else "@cf/black-forest-labs/flux-1-schnell"
    model = args.model or os.environ.get("CLOUDFLARE_IMAGE_MODEL", default_model)
    if args.reference and "flux-2-klein" not in model:
        print("Reference images require --model @cf/black-forest-labs/flux-2-klein-4b.", file=sys.stderr)
        return 2

    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reference_bytes: bytes | None = None
    reference_path: str | None = None
    if args.reference:
        ref_file = Path(args.reference)
        if not ref_file.is_absolute():
            ref_file = ROOT / ref_file
        if not ref_file.exists():
            print(f"Reference file not found: {ref_file}", file=sys.stderr)
            return 2
        try:
            reference_bytes = prepare_reference(ref_file)
        except (OSError, RuntimeError) as error:
            print(f"Could not prepare reference image: {error}", file=sys.stderr)
            return 2
        reference_path = str(ref_file.relative_to(ROOT)) if ref_file.is_relative_to(ROOT) else str(ref_file)
        print(f"Using style reference: {reference_path}")

    for shot in shots:
        shot_id = shot["id"]
        output_path = OUTPUT_DIR / f"{shot_id}.jpg"
        if output_path.exists() and not args.overwrite:
            print(f"Skipping {shot_id}; {output_path.relative_to(ROOT)} already exists.")
            continue

        reference_instruction = (
            "Use image 0 as the family and visual-style reference. Preserve the same five adults and "
            "Ethiopian Christmas design; create only the shot described below.\n\n"
            if reference_bytes
            else ""
        )
        prompt = f"{reference_instruction}{storyboard['style']}\n\nShot: {shot['image_prompt']}"
        started = time.perf_counter()
        try:
            image_bytes, latency_ms = generate_image(url, token, model, prompt, reference_bytes)
            output_path.write_bytes(image_bytes)
            append_log({
                "stage": "keyframe",
                "provider": "cloudflare_workers_ai",
                "model": model,
                "shot_id": shot_id,
                "parameters": {"prompt": prompt, "reference_sheet": reference_path},
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
                "parameters": {"prompt": prompt, "reference_sheet": reference_path},
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
