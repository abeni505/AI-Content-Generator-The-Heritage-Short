# Design

## Audience
Family and friends who celebrate Christmas with us, including people who may not be able to join the gathering in person.

## Intent
By the end, viewers should feel the warmth of being together and understand that the surprise gift exchange is meaningful because each gift carries someone's thought and care.

## Story
Two or three weeks before Christmas Eve, everyone writes their name on a slip of paper. The slips are shuffled, and each person takes someone else's name. They secretly prepare a present for that person. At the Christmas Eve ceremony, Father begins by giving his present to the person whose name he drew. That recipient gives their own present to the person they drew, and the exchange continues until everyone has received a surprise. The film closes on the joy of giving and being remembered.

## Visual approach
Use warm, intimate Christmas Eve imagery with golden light, reds and evergreen accents. Keep generated people non-identifiable and focus on gifts, hands, and the atmosphere unless consent for a person's likeness is recorded in ETHICS.md. Add all titles and the AI disclosure end card during assembly rather than generating text in images.

## Language and draft status
The narration is drafted in Amharic, with English subtitle text beside each shot in storyboard.json. Family listeners reviewed the radio cut. The narration is still a draft: the pace needs to be slower, and pronunciation of "ገና" and "ልማድ" needs further review. The visuals use non-identifiable silhouettes and hands; do not generate Father's recognizable likeness without recording his informed consent in ETHICS.md.

## Audience test 1: radio cut
Conducted 2026-11-26. Narration-only WAV played for three intended viewers (family members).

**Listener comments**
- Listeners 1 and 2 (of 3): "ገና" was pronounced incorrectly and sounded unlike the usual pronunciation.
- Listener 3: no comment on pronunciation.
- Listener 1: the storytelling felt a bit fast; a slower pace would be better.
- Listener 2: "ልማድ" was not pronounced correctly.
- Listener 3: the narration should say "የገና ዋዜማ," not "በገና ዋዜማ."

**Changes made as a result**
- Corrected shot 5 in storyboard.json to say "የገና ዋዜማ"; its English subtitle already matches.
- Updated the TTS style instruction in `pipeline/generate_narration.py` to request a noticeably slower, unhurried pace and the familiar Amharic pronunciation of "ገና". Each style change creates a new cached WAV.
- The pronunciation of "ልማድ" remains unresolved; ask a fluent Amharic speaker for a precise pronunciation cue before changing the wording.
- Added a ninth closing shot with a family reflection. The revised narration is 71 seconds; the storyboard runtime is 81 seconds.

**Follow-up review**
- The three listeners said the revised cut is better, but the pronunciation issue is not completely solved. Keep the narration as a draft and revisit pronunciation before final delivery.

## Audience test 2: near-final cut
Not done yet. Show the near-final film to at least three intended viewers. Record their actual comments and resulting changes here.
