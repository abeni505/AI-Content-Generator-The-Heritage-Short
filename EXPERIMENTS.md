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
