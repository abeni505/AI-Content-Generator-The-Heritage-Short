# Measured costs and runtime

Measurements below come from the 50 entries currently in `runs.jsonl`. They describe this project run, not a guaranteed future provider price or latency. API `cost_usd` values are mostly unavailable, so actual provider billing must be checked in each account dashboard.

| Stage | Measured calls | Typical latency | GPU time | Cost evidence |
|---|---:|---:|---:|---|
| Cloudflare keyframes | 19 successful generation calls | 6.7 s average; 2.7–13.3 s range | 0 min locally | About **$0.018 list-price equivalent**, estimated from 5 FLUX.1 schnell 1024×1024 outputs and 14 FLUX.2 Klein 1024×1024 outputs with one 512×512 reference input each. Actual account billing/free allowance is not recorded. |
| Gemini narration | 4 successful TTS calls | 23.2 s average; 18.1–29.2 s range | 0 min locally | About **$0.052 audio-output list-price equivalent** for 232.63 seconds of generated WAVs at the current paid rate; text-input tokens are excluded. The free tier may apply; actual account billing is not recorded. |
| FFmpeg pan-and-zoom | 18 clips across both formats | 2.6 s average per clip; 46.5 s total measured render time | 0 min (CPU only) | $0 provider charge; local electricity not measured. |
| ACE-Step music | 1 selected 155-second score | Generation latency not recorded | 0 min on this computer (hosted web generation) | ACE Music stated ACE-Step 1.5 XL uses no generation credits when used through its hosted page. Confirm the current service terms and account usage. |
| Assembly | 2 final exports | Measured locally by FFmpeg; not logged as a stage | 0 min GPU | $0 provider charge; local CPU time/electricity not logged. |

Both current exports measure -14.7 LUFS integrated loudness and -1.1 dBFS true peak after the EBU R128 normalization pass.

## List-price equivalent

Provider prices change. The estimates above use published list prices checked on 2026-11-26: [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) and [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing). Image estimate assumes the logged 1024×1024 output dimensions and one 512×512 reference tile for each Klein call. TTS estimate counts generated audio duration only and excludes text input. These are list-price equivalents before any free tier or account credits, not actual charges. `runs.jsonl` uses `cost_usd: null` where the provider did not return billing data; check account dashboards for actual usage.

## Reproduction requirements

- `make film` uses the committed narration, score, keyframes, and clips; it makes no model calls.
- `make regenerate` may call Gemini and Cloudflare when required assets are missing or forced. A local `.env` is required for those calls and is excluded from Git.
- Replacing the music is a separate manual input; hosted ACE Music did not expose an API in this workflow.
