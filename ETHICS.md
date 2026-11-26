# Ethics, consent, labels, and licences

## People and consent

- The film depicts a family tradition. The generated images use non-identifiable, illustrated people; no identifiable family photograph, face, or likeness was supplied to image generation.
- Narration is synthetic Gemini TTS using the script in `storyboard.json`. It does not imitate a family member's recorded voice.
- No identifiable real-person likeness or voice was generated, so there is no individual likeness/voice consent record to attach. If that changes, obtain and record informed consent before generating or publishing that person's likeness or voice.
- Prompts include family composition and adult age ranges, but not personal names or contact details. `.env` credentials are ignored by Git; never commit them.

## AI disclosure

- Both exports contain an end card: “AI-assisted short film / Story and narration: human-directed / Images and music: AI-generated.”
- When publishing on a service that offers an AI/synthetic-media disclosure, enable that platform label as well. The end card does not replace the platform's disclosure control.
- Preserve any provenance metadata or watermarks produced by a provider. This project does not add C2PA metadata.

## Models and terms to review before redistribution

| Use | Service/model | Rights and source |
|---|---|---|
| Keyframes | Cloudflare Workers AI, `@cf/black-forest-labs/flux-2-klein-4b` | Hosted inference; review the current [Cloudflare terms](https://www.cloudflare.com/terms/) and [Workers AI documentation](https://developers.cloudflare.com/workers-ai/). The model output's exact licensing status was not independently established for this project. |
| Narration | Google Gemini API TTS, `gemini-3.8-flash-tts` | Review the current [Gemini API additional terms](https://ai.google.dev/gemini-api/terms) and Google's privacy/data-use terms before sending sensitive material. |
| Score | ACE-Step 1.5 XL through ACE Music hosted web service | The [ACE Music ACE-Step page](https://acemusic.ai/ace-step/) states personal and commercial use of ACE-Step outputs is permitted under its terms, subject to rights in inputs and third-party claims. The chosen track is `outputs/audio/selected_original_score.mp3`. |
| Moving shots and assembly | FFmpeg | Local software; review the installed FFmpeg build's license configuration if redistributing binaries. This repository invokes FFmpeg and does not bundle it. |

The score and imagery are model-generated outputs. This document records the workflow and links to the service terms; it is not a legal determination that every output is copyrightable or free of third-party rights. Recheck current terms before commercial distribution.
