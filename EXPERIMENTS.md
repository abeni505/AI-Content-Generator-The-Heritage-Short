# Experiments

## Reference sheet and shot diversity — 2026-11-26

- **Hypothesis:** A family/style reference image will keep the five family members and Ethiopian Christmas details consistent across shots.
- **Change:** Passed the reference sheet to FLUX.2 Klein and repeated the family/style description in every shot prompt.
- **Result:** The family and visual style stayed consistent, but shots 3, 5, 6, 7, and 9 repeated a similar wide family composition. Shots 4 and 8 were visually distinct.
- **Next change:** Put each shot's action and framing first, tell the model to use the reference only for identity and style, and regenerate the repetitive shots. Review shot 3 before regenerating the rest.
- **Check:** The revised shot 3 was regenerated and the user confirmed that its close-up composition is distinct. Proceed with shots 5, 6, 7, and 9.

## FFmpeg motion fallback — 2026-11-26

- **Hypothesis:** Slow pan-and-zoom motion can keep production moving while the Kaggle GPU session remains unavailable.
- **Change:** Rendered each approved keyframe as a nine-second 24 fps clip at 1280×720 and 720×1280 using FFmpeg, preserving the complete image over a blurred background fill.
- **Result:** All 18 clips rendered successfully. A representative clip is 9 seconds in each aspect ratio. Rendering takes about 2.4–2.8 seconds per clip and uses no GPU.
- **Limit:** This is restrained still-image motion, not generated character animation. The vertical version has blurred fill above and below the square artwork.
- **Decision:** Use these clips as the working assembly and continue to original score generation; replace individual clips with generated motion only if a GPU runtime becomes available in time.

## Two-format film draft — 2026-11-26

- **Change:** Joined the 9 approved clips in each aspect ratio, burned in English subtitles, mixed the Amharic narration with ducked placeholder music, and appended a three-second AI disclosure card.
- **Result:** `outputs/final/heritage_short_16x9.mp4` is 1280×720 and `outputs/final/heritage_short_9x16.mp4` is 720×1280. Both are 84 seconds, within the brief's 60–90 second target.
- **Limit:** The first draft used a temporary synthetic placeholder. Captions follow storyboard shot timing and need a full playback review.

## Original ACE-Step score — 2026-11-26

- **Change:** Generated an instrumental score with ACE-Step 1.5 XL through ACE Music's hosted browser generator after the Hugging Face Space reached its limit and local model downloads proved too slow for the deadline.
- **Output:** `outputs/audio/selected_original_score.mp3` (155 seconds). The assembler uses the first 84 seconds under the narration and adds its standard ducking and fade.
- **Selection:** One candidate was generated and selected after listening; the user approved the score in the assembled film. The brief suggests auditioning several candidates, so this is a documented shortcut rather than a multi-candidate comparison.
- **Result:** Rebuilt both deliverables in `outputs/final/original_score/`: 1280×720 landscape and 720×1280 portrait, each 84 seconds with stereo audio.
- **Review:** The user reviewed both exports and approved the result after noticing and reporting that the audio dropped out at 1:10.
- **Correction:** Padded the side-chain narration reference to the full film duration so the score continues beneath the three-second end card. Rebuilt both exports; each audio stream now runs for the full 84 seconds.
- **Audience test:** The user reports that all three intended viewers liked the revised film; no specific changes were reported. See `DESIGN.md`.
- **Normalization follow-up:** Added an EBU R128 `loudnorm` pass targeting -14 LUFS integrated loudness and -1 dB true peak. Both rebuilt exports measure -14.7 LUFS integrated and -1.1 dBFS true peak.
