"""Assemble the storyboard clips into English-subtitled final-format drafts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD = ROOT / "storyboard.json"
NARRATION = ROOT / "outputs/audio/narration_350bd7a74de3581d.wav"
MUSIC = ROOT / "outputs/audio/placeholder_score.wav"
CLIPS = ROOT / "outputs/clips"
OUTPUTS = ROOT / "outputs/final"
FPS = 24
CARD_SECONDS = 3


def timestamp(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    whole, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02},{millis:03}"


def write_subtitles(shots: list[dict], path: Path, wrap_width: int) -> None:
    elapsed = 0.0
    cues = []
    for index, shot in enumerate(shots, start=1):
        caption = shot.get("subtitle_en", "").strip()
        if caption:
            wrapped = "\n".join(textwrap.wrap(caption, width=wrap_width))
            # Shot timing keeps the translated caption aligned with its image.
            start = elapsed + 0.15
            end = elapsed + float(shot["duration_seconds"]) - 0.2
            cues.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{wrapped}")
        elapsed += float(shot["duration_seconds"])
    path.write_text("\n\n".join(cues) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble both aspect ratios with English captions and an AI disclosure card.")
    parser.add_argument("--music", type=Path, default=MUSIC, help="Final instrumental score WAV/MP3; defaults to the temporary placeholder bed")
    parser.add_argument("--narration", type=Path, default=NARRATION)
    parser.add_argument("--clips", type=Path, default=CLIPS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUTS)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg is not on PATH.", file=sys.stderr)
        return 2
    if not args.narration.is_file() or not args.music.is_file():
        print("Narration or music input file is missing.", file=sys.stderr)
        return 2
    try:
        storyboard = json.loads(STORYBOARD.read_text(encoding="utf-8"))
        shots = storyboard["shots"]
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(f"Could not load storyboard: {error}", file=sys.stderr)
        return 1

    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    temp = ROOT / "outputs/tmp/film_assembly"
    temp.mkdir(parents=True, exist_ok=True)
    total_duration = sum(float(shot["duration_seconds"]) for shot in shots)
    final_duration = total_duration + CARD_SECONDS
    formats = {
        "16x9": (1280, 720, 62, 16),
        "9x16": (720, 1280, 28, 10),
    }

    for aspect, (width, height, wrap_width, font_size) in formats.items():
        clip_paths = [args.clips / aspect / f"{shot['id']}.mp4" for shot in shots]
        missing = [str(path) for path in clip_paths if not path.is_file()]
        if missing:
            print("Missing clips:\n" + "\n".join(missing), file=sys.stderr)
            return 1

        listing = temp / f"{aspect}_clips.txt"
        listing.write_text("".join(f"file '{path.resolve()}'\n" for path in clip_paths), encoding="utf-8")
        subtitles = temp / f"{aspect}.srt"
        write_subtitles(shots, subtitles, wrap_width)
        style = (
            f"FontName=Arial,FontSize={font_size},Bold=1,Outline=2,Shadow=1,"
            "Alignment=2,MarginV=42,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000"
        )
        caption_filter = f"subtitles=filename={subtitles.as_posix()}:force_style={style.replace(',', r'\,')}"
        card_text = temp / f"{aspect}_endcard.txt"
        card_text.write_text("AI-assisted short film\nStory and narration: human-directed\nImages and music: AI-generated", encoding="utf-8")
        card_filter = (
            f"drawtext=font='Arial':textfile='{card_text.as_posix()}':"
            f"fontcolor=white:fontsize={max(22, font_size - 2)}:line_spacing=14:"
            "x=(w-text_w)/2:y=(h-text_h)/2"
        )
        output = args.output_dir / f"heritage_short_{aspect}.mp4"
        filter_graph = (
            f"[0:v]{caption_filter},setsar=1[main];"
            f"[1:v]{card_filter},setsar=1[card];"
            "[main][card]concat=n=2:v=1:a=0[v];"
            "[2:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[narr][voice];"
            "[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.24[music];"
            "[music][voice]sidechaincompress=threshold=0.025:ratio=8:attack=25:release=650[ducked];"
            "[narr][ducked]amix=inputs=2:duration=longest:dropout_transition=1,"
            "alimiter=limit=0.95,afade=t=out:st=" + str(final_duration - 2) + ":d=2[a]"
        )
        command = [
            ffmpeg, "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r={FPS}:d={CARD_SECONDS}",
            "-i", str(args.narration), "-stream_loop", "-1", "-i", str(args.music),
            "-filter_complex", filter_graph, "-map", "[v]", "-map", "[a]",
            "-t", str(final_duration), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(output),
        ]
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
        print(f"Created {output.relative_to(ROOT)} ({final_duration:.0f}s, {width}×{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
