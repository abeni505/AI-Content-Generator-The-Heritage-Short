"""Small, non-secret smoke tests for Gemini TTS and Cloudflare Workers AI.

Load credentials from environment variables (for example by sourcing a local
.env file). Every attempted provider call is appended to runs.jsonl.
"""

from __future__ import annotations

import base64
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "runs.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "audio"
IMAGE_DIR = ROOT / "outputs" / "keyframes"


def log_call(entry: dict) -> None:
    entry["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def request_json(url: str, headers: dict, payload: dict) -> tuple[dict, float]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result, round((time.perf_counter() - started) * 1000)


def run_gemini_tts() -> None:
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
    prompt = "This is a short narration audio smoke test."
    payload = {
        "model": model,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": prompt,
                "annotations": [{"type": "speech_metadata", "style": "clear, calm narration"}],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": "Kore"}]},
    }
    started = time.perf_counter()
    try:
        result, latency_ms = request_json(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            payload,
        )
        # The SDK exposes output_audio.data, while raw REST JSON puts audio
        # blocks under steps[].content[] (see the Gemini TTS REST response).
        interaction = result.get("interaction", result)
        audio_b64 = interaction.get("output_audio", {}).get("data")
        if not audio_b64:
            for step in interaction.get("steps", []):
                if step.get("type") != "model_output":
                    continue
                for content in step.get("content", []):
                    if content.get("type") == "audio" and content.get("data"):
                        audio_b64 = content["data"]
                        break
                if audio_b64:
                    break
        if not audio_b64:
            raise RuntimeError("Gemini returned no output_audio.data field")
        audio_bytes = base64.b64decode(audio_b64)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "smoke_gemini_tts.wav"
        output_path.write_bytes(audio_bytes)
        log_call({
            "stage": "smoke_test",
            "provider": "google_gemini",
            "model": model,
            "parameters": {"voice": "Kore", "response_format": "audio"},
            "seed": None,
            "latency_ms": latency_ms,
            "cost_usd": None,
            "cost_note": "Check Google AI Studio usage; free-tier availability depends on account and model.",
            "status": "success",
            "output": str(output_path.relative_to(ROOT)),
        })
        print(f"Gemini TTS: OK ({latency_ms} ms); audio saved to {output_path.relative_to(ROOT)}")
    except Exception as error:
        latency_ms = round((time.perf_counter() - started) * 1000)
        status = error.code if isinstance(error, urllib.error.HTTPError) else None
        if isinstance(error, urllib.error.HTTPError):
            detail = error.read().decode("utf-8", errors="replace")[:1200]
        else:
            detail = str(error.reason) if isinstance(error, urllib.error.URLError) else str(error)
        log_call({
            "stage": "smoke_test",
            "provider": "google_gemini",
            "model": model,
            "parameters": {"voice": "Kore", "response_format": "audio"},
            "seed": None,
            "latency_ms": latency_ms,
            "cost_usd": None,
            "status": "error",
            "http_status": status,
            "error_type": type(error).__name__,
            "error_detail": detail,
        })
        raise RuntimeError(f"Gemini TTS failed ({type(error).__name__}; HTTP {status or 'n/a'}): {detail}. See runs.jsonl.") from error


def run_cloudflare_image() -> None:
    model = os.environ.get("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    payload = {
        "prompt": "A simple warm holiday candle on a table, soft golden light, no people, no text",
    }
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    started = time.perf_counter()
    try:
        result, latency_ms = request_json(
            url,
            {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"},
            payload,
        )
        image_b64 = result.get("result", {}).get("image")
        if not image_b64:
            raise RuntimeError("Cloudflare returned no result.image field")
        image_bytes = base64.b64decode(image_b64)
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        output_path = IMAGE_DIR / "smoke_cloudflare.jpg"
        output_path.write_bytes(image_bytes)
        log_call({
            "stage": "smoke_test",
            "provider": "cloudflare_workers_ai",
            "model": model,
            "parameters": {"prompt": payload["prompt"]},
            "seed": None,
            "latency_ms": latency_ms,
            "cost_usd": None,
            "cost_note": "Check Workers AI usage in the Cloudflare dashboard.",
            "status": "success",
            "output": str(output_path.relative_to(ROOT)),
        })
        print(f"Cloudflare image: OK ({latency_ms} ms); image saved to {output_path.relative_to(ROOT)}")
    except Exception as error:
        latency_ms = round((time.perf_counter() - started) * 1000)
        status = error.code if isinstance(error, urllib.error.HTTPError) else None
        if isinstance(error, urllib.error.HTTPError):
            detail = error.read().decode("utf-8", errors="replace")[:1200]
        else:
            detail = str(error.reason) if isinstance(error, urllib.error.URLError) else str(error)
        log_call({
            "stage": "smoke_test",
            "provider": "cloudflare_workers_ai",
            "model": model,
            "parameters": {"prompt": payload["prompt"]},
            "seed": None,
            "latency_ms": latency_ms,
            "cost_usd": None,
            "status": "error",
            "http_status": status,
            "error_type": type(error).__name__,
            "error_detail": detail,
        })
        raise RuntimeError(f"Cloudflare image call failed ({type(error).__name__}; HTTP {status or 'n/a'}): {detail}. See runs.jsonl.") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test Gemini TTS and/or Cloudflare Workers AI.")
    parser.add_argument("--only", choices=["all", "gemini", "cloudflare"], default="all")
    only = parser.parse_args().only
    required = []
    if only in ("all", "gemini"):
        required.append("GEMINI_API_KEY")
    if only in ("all", "cloudflare"):
        required.extend(["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"])
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        print("Set them in your local .env file; do not commit or share that file.", file=sys.stderr)
        return 2

    try:
        if only in ("all", "gemini"):
            run_gemini_tts()
        if only in ("all", "cloudflare"):
            run_cloudflare_image()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Smoke-test log: {LOG_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
