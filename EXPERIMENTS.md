# Experiments

## Reference sheet and shot diversity — 2026-11-26

- **Hypothesis:** A family/style reference image will keep the five family members and Ethiopian Christmas details consistent across shots.
- **Change:** Passed the reference sheet to FLUX.2 Klein and repeated the family/style description in every shot prompt.
- **Result:** The family and visual style stayed consistent, but shots 3, 5, 6, 7, and 9 repeated a similar wide family composition. Shots 4 and 8 were visually distinct.
- **Next change:** Put each shot's action and framing first, tell the model to use the reference only for identity and style, and regenerate the repetitive shots. Review shot 3 before regenerating the rest.
- **Check:** The revised shot 3 was regenerated and the user confirmed that its close-up composition is distinct. Proceed with shots 5, 6, 7, and 9.
