# Failures and recoveries

## Radio-cut FFmpeg filter graph — 2026-11-26

- **Failure:** The first assembly failed because the narration stream label was reused for both side-chain ducking and the final mix; FFmpeg reported that the filter graph could not match the stream.
- **Fix:** Split the narration with `asplit` into separate voice and mix inputs, then reran the assembly successfully.
- **Result:** `outputs/final/radio_cut.mp4` was created at 81 seconds.
