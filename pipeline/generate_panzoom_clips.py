"""Create moving shots from storyboard keyframes using FFmpeg's zoompan fallback.

The brief explicitly accepts slow pan-and-zoom animation when GPU video
generation is unavailable. Each shot is rendered in vertical and horizontal
formats; the original still is centered over a blurred fill background to
avoid cropping or stretching the square keyframes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_PATH = ROOT / "storyboard.json"
LOG_PATH = ROOT / "runs.jsonl"
KEYFRAME_DIR = ROOT / "outputs" / "keyframes"
CLIP_DIR = ROOT / "outputs" / "clips"
FPS = 24


def append_log(record: dict) -> None:
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def filter_graph(width: int, height: int, index: int) -> str:
    foreground = min(width, height)
    frames = 9 * FPS
    if index % 2:
        x_expr = "(iw-iw/zoom)*0.5"
        y_expr = f"(ih-ih/zoom)*on/{frames - 1}"
    else:
        x_expr = f"(iw-iw/zoom)*on/{frames - 1}"
        y_expr = "(ih-ih/zoom)*0.5"

    return (
        f"[0:v]split[bgraw][fgraw];"
        f"[bgraw]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=18:8[bg];"
        f"[fgraw]scale={foreground}:{foreground},"
        f"zoompan=z='1+0.08*on/{frames - 1}':x='{x_expr}':y='{y_expr}':"
        f"d=1:s={foreground}x{foreground}:fps={FPS}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,format=yuv420p[v]"
    )


def render_clip(ffmpeg: str, image_path: Path, output_path: Path, width: int, height: int, duration: float, index: int) -> tuple[int, int, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-filter_complex", filter_graph(width, height, index),
        "-map", "[v]",
        "-t", str(duration),
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    latency_ms = round((time.perf_counter() - started) * 1000)
    return result.returncode, latency_ms, result.stderr[-1500:] if result.returncode else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Animate keyframes with slow FFmpeg pan-and-zoom movement.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate clips that already exist")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg is not on PATH.", file=sys.stderr)
        return 2
    try:
        storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read storyboard.json: {error}", file=sys.stderr)
        return 1

    aspects = {
        "16x9": (1280, 720),
        "9x16": (720, 1280),
    }
    for index, shot in enumerate(storyboard.get("shots", [])):
        shot_id = shot["id"]
        image_path = KEYFRAME_DIR / f"{shot_id}.jpg"
        if not image_path.is_file():
            print(f"Missing keyframe: {image_path.relative_to(ROOT)}", file=sys.stderr)
            return 1

        for aspect, (width, height) in aspects.items():
            output_path = CLIP_DIR / aspect / f"{shot_id}.mp4"
            if output_path.exists() and not args.overwrite:
                print(f"Skipping {output_path.relative_to(ROOT)}; it already exists.")
                continue
            duration = float(shot["duration_seconds"])
            return_code, latency_ms, error_detail = render_clip(ffmpeg, image_path, output_path, width, height, duration, index)
            if return_code:
                append_log({
                    "stage": "moving_shot",
                    "provider": "local_ffmpeg",
                    "model": "zoompan",
                    "shot_id": shot_id,
                    "parameters": {"aspect_ratio": aspect, "duration_seconds": duration, "fps": FPS},
                    "latency_ms": latency_ms,
                    "cost_usd": 0,
                    "status": "error",
                    "error_detail": error_detail,
                })
                print(f"Failed {shot_id} ({aspect}):\n{error_detail}", file=sys.stderr)
                return 1

            append_log({
                "stage": "moving_shot",
                "provider": "local_ffmpeg",
                "model": "zoompan",
                "shot_id": shot_id,
                "parameters": {"aspect_ratio": aspect, "duration_seconds": duration, "fps": FPS, "movement": "slow pan and 8% zoom"},
                "latency_ms": latency_ms,
                "cost_usd": 0,
                "status": "success",
                "output": str(output_path.relative_to(ROOT)),
            })
            print(f"Rendered {output_path.relative_to(ROOT)} ({latency_ms} ms)")

    print(f"Moving-shot clips saved under {CLIP_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
