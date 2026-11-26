# Failures and recoveries

## Provider smoke-test failures — 2026-11-26

- **Gemini TTS:** The first attempts hit a wrong host/response-shape issue, a local certificate-chain error, and a response without the expected audio field. The request/response handling was corrected and later TTS smoke tests succeeded. Errors and latency are preserved in `runs.jsonl`.
- **Cloudflare image smoke test:** The initial request included an unsupported `seed` property and returned HTTP 400. Removed the unsupported field; the image smoke test then succeeded. The failed request remains in the log.

## Radio-cut FFmpeg filter graph — 2026-11-26

- **Failure:** The first assembly failed because the narration stream label was reused for both side-chain ducking and the final mix; FFmpeg reported that the filter graph could not match the stream.
- **Fix:** Split the narration with `asplit` into separate voice and mix inputs, then reran the assembly successfully.
- **Result:** `outputs/final/radio_cut.mp4` was created at 81 seconds.

## Kaggle GPU session startup — 2026-11-26

- **Failure:** The Kaggle notebook stayed on “Draft Session Starting” for more than two hours, including after a restart.
- **Recovery:** The brief allows FFmpeg slow pan/zoom when video generation is unavailable. Rendered all nine keyframes into both required aspect ratios with `pipeline/generate_panzoom_clips.py`.
- **Result:** 18 clips completed locally without a GPU; the project can proceed to assembly while Kaggle is unavailable.

## ACE-Step local install and model download — 2026-11-26

- **Failure:** The first Git clone was interrupted; a retry completed. Dependency setup then exposed a Windows-only Flash Attention wheel URL on macOS, and local ACE-Step model weights were downloading at roughly 16–18 KB/s with an impractical multi-day ETA.
- **Recovery:** Stopped the local model download and used ACE Music's hosted ACE-Step 1.5 XL interface instead. The chosen score was saved locally and included in both exports.
- **Limit:** This score-generation step is manual and is not callable by `make regenerate`; supply a new score file to use different music.

## Music stopped when narration ended — 2026-11-26

- **Failure:** In the original-score film exports, the ducking side-chain ended with the 71-second narration, so the final 13 seconds, including the end card, were silent.
- **Fix:** Padded the side-chain reference signal through the full 84-second film, then rebuilt both aspect ratios.
- **Check:** The landscape export's audio stream now measures 84 seconds; playback confirmed music continues through the end card.
