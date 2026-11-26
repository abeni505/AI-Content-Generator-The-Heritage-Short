"""Create a small, original synthetic music bed for the Phase 1 radio cut.

This is only a temporary placeholder. Replace it with the selected ACE-Step
score during Phase 2.
"""

from __future__ import annotations

import argparse
import math
import wave
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "audio" / "placeholder_score.wav"
SAMPLE_RATE = 22050


def frequency(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a gentle synthetic placeholder score WAV.")
    parser.add_argument("--duration", type=float, default=81.0, help="Track length in seconds (default: 81)")
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error("--duration must be positive")

    # A slow, warm progression with a very soft bell-like motif.
    chords = [
        (48, 55, 60, 64),  # C
        (43, 50, 55, 59),  # G
        (45, 52, 57, 60),  # Am
        (41, 48, 53, 57),  # F
        (50, 57, 62, 65),  # Dm
        (43, 50, 55, 59),  # G
        (41, 48, 53, 57),  # F
        (48, 55, 60, 64),  # C
    ]
    melody = [72, 76, 79, 76, 74, 72, 67, 72, 76, 79, 81, 79, 76, 74, 72, 67]
    block_seconds = args.duration / len(chords)
    total_frames = round(args.duration * SAMPLE_RATE)
    samples = array("h")

    for frame in range(total_frames):
        t = frame / SAMPLE_RATE
        chord_index = min(int(t / block_seconds), len(chords) - 1)
        within = t - chord_index * block_seconds
        edge = min(1.0, within / 1.6, (block_seconds - within) / 1.6)
        pad = 0.0
        for note in chords[chord_index]:
            hz = frequency(note)
            pad += math.sin(2.0 * math.pi * hz * t)
            pad += 0.18 * math.sin(2.0 * math.pi * hz * 2.0 * t)

        beat = t % 2.4
        bell = 0.0
        if beat < 1.1:
            note = melody[int(t / 2.4) % len(melody)]
            bell = math.sin(2.0 * math.pi * frequency(note) * beat) * math.exp(-3.8 * beat)

        value = (0.115 * edge * pad / 4.72) + (0.035 * bell)
        value = max(-0.85, min(0.85, value))
        samples.append(round(value * 32767))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())

    print(f"Placeholder score saved: {OUTPUT.relative_to(ROOT)} ({args.duration:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
