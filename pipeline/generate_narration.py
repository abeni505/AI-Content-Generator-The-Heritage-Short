"""Generate a cached Amharic narration WAV from storyboard.json using Gemini TTS."""

from __future__ import annotations

import base64
import hashlib
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
OUTPUT_DIR = ROOT / "outputs" / "audio"
STYLE = "Warm, clear Amharic storytelling, natural speaking pace, gentle and heartfelt, pronounce the Amharic text naturally."


def append_log(record: dict) -> None:
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_audio(response: dict) -> str | None:
    interaction = response.get("interaction", response)
    convenience_audio = interaction.get("output_audio", {}).get("data")
    if convenience_audio:
        return convenience_audio
    for step in interaction.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for content in step.get("content", []):
            if content.get("type") == "audio" and content.get("data"):
                return content["data"]
    return None


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Load it from your local .env file first.", file=sys.stderr)
        return 2

    try:
        storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read valid storyboard.json: {error}", file=sys.stderr)
        return 1

    lines = [shot["narration"].strip() for shot in storyboard["shots"] if shot["narration"].strip()]
    if not lines:
        print("No narration lines found in storyboard.json.", file=sys.stderr)
        return 1

    transcript = "\n\n".join(lines)
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
    voice = os.environ.get("GEMINI_TTS_VOICE", "Kore")
    cache_key = hashlib.sha256(
        json.dumps({"model": model, "voice": voice, "style": STYLE, "text": transcript}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    output_path = OUTPUT_DIR / f"narration_{cache_key}.wav"
    if output_path.exists():
        print(f"Narration already exists; using cached file {output_path.relative_to(ROOT)}")
        return 0

    payload = {
        "model": model,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": transcript,
                "annotations": [{"type": "speech_metadata", "style": STYLE}],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    base_record = {
        "stage": "narration",
        "provider": "google_gemini",
        "model": model,
        "parameters": {"voice": voice, "style": STYLE, "line_count": len(lines), "text_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest()},
        "seed": None,
        "cost_usd": None,
        "cost_note": "Check Google AI Studio usage for actual billing/free-tier usage.",
    }
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            result = json.loads(response.read().decode("utf-8"))
        latency_ms = round((time.perf_counter() - started) * 1000)
        audio_b64 = extract_audio(result)
        if not audio_b64:
            raise RuntimeError("Gemini response contained no audio block in steps[].content[].data")
        audio_bytes = base64.b64decode(audio_b64)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)
        append_log({
            **base_record,
            "latency_ms": latency_ms,
            "status": "success",
            "output": str(output_path.relative_to(ROOT)),
        })
        print(f"Narration saved to {output_path.relative_to(ROOT)} ({latency_ms} ms)")
        print("Listen to the WAV and ask a fluent Amharic speaker to review pronunciation before using it in the radio cut.")
        return 0
    except Exception as error:
        latency_ms = round((time.perf_counter() - started) * 1000)
        status = error.code if isinstance(error, urllib.error.HTTPError) else None
        if isinstance(error, urllib.error.HTTPError):
            detail = error.read().decode("utf-8", errors="replace")[:1200]
        elif isinstance(error, urllib.error.URLError):
            detail = str(error.reason)
        else:
            detail = str(error)
        append_log({
            **base_record,
            "latency_ms": latency_ms,
            "status": "error",
            "http_status": status,
            "error_type": type(error).__name__,
            "error_detail": detail,
        })
        print(f"Narration generation failed ({type(error).__name__}; HTTP {status or 'n/a'}): {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
