"""Assemble the Amharic narration over placeholder music on a black screen."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NARRATION = ROOT / "outputs" / "audio" / "narration_350bd7a74de3581d.wav"
DEFAULT_MUSIC = ROOT / "outputs" / "audio" / "placeholder_score.wav"
DEFAULT_OUTPUT = ROOT / "outputs" / "final" / "radio_cut.mp4"


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a black-screen radio cut with narration and a placeholder score.")
    parser.add_argument("--narration", type=Path, default=DEFAULT_NARRATION)
    parser.add_argument("--music", type=Path, default=DEFAULT_MUSIC)
    parser.add_argument("--duration", type=float, default=81.0, help="Storyboard duration in seconds")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg is not on PATH. Finish installing it, then rerun this command.", file=sys.stderr)
        return 2
    for path in (args.narration, args.music):
        if not path.is_file():
            print(f"Input file not found: {path}", file=sys.stderr)
            return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    filter_graph = (
        "[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[narr][voice];"
        "[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.24[music];"
        "[music][voice]sidechaincompress=threshold=0.025:ratio=8:attack=25:release=650[ducked];"
        "[narr][ducked]amix=inputs=2:duration=longest:dropout_transition=1,"
        "alimiter=limit=0.95[aout]"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1280x720:r=24:d={args.duration}",
        "-i", str(args.narration),
        "-i", str(args.music),
        "-filter_complex", filter_graph,
        "-map", "0:v:0",
        "-map", "[aout]",
        "-t", str(args.duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(args.output),
    ]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        return result.returncode
    print(f"Radio cut saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
