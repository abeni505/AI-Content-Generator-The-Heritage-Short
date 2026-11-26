# The Gift We Couldn't Guess

A short-film project about our Christmas Eve surprise gift exchange. The storyboard is in `storyboard.json`.

## Local provider smoke tests

The smoke script makes one Gemini text-to-speech request and one Cloudflare Workers AI image-generation request. It saves the sample outputs under `outputs/` and appends latency, parameters, and status to `runs.jsonl`.

1. Copy `.env.example` to `.env` and fill in credentials locally. Never commit `.env`.
2. Load the environment variables and run:

   ```sh
   set -a
   source .env
   set +a
   python3 pipeline/smoke_test.py
   ```

The script uses standard Python libraries. Gemini model, Cloudflare account, and model settings can be changed in `.env`. The smoke prompt is generic and contains no family details. Check each provider's dashboard for actual usage and cost.

## Validate the storyboard

Create and activate a local Python environment, install the schema validator, then validate the storyboard:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pipeline/validate_storyboard.py
```

The validator checks the JSON Schema, unique shot IDs, and a total runtime of 60–90 seconds.

## Generate narration

After reviewing the Amharic narration in `storyboard.json`, load the local environment and run:

```sh
set -a
source .env
set +a
python pipeline/generate_narration.py
```

This makes one Gemini TTS call for the complete narration, saves the WAV under `outputs/audio/`, and logs the call to `runs.jsonl`. The output filename is based on a hash of the narration and settings, so repeating the command with the same inputs reuses the cached file.

## Assemble the Phase 1 radio cut

Create a temporary, original synthetic bed, then combine it with the Amharic narration over a black screen. Replace this placeholder bed with the selected ACE-Step score during Phase 2.

```sh
python3 pipeline/create_placeholder_score.py --duration 81
python3 pipeline/assemble_radio_cut.py
```

The MP4 is saved to `outputs/final/radio_cut.mp4`.

## Generate storyboard keyframes

Load the local environment, then generate one image first so you can review the look before using the image API for all shots:

```sh
set -a
source .env
set +a
python3 pipeline/generate_keyframes.py --shot shot_01
```

Review `outputs/keyframes/shot_01.jpg`. Generate a family/style reference sheet before the other shots. FLUX.1 schnell accepts text prompts only; FLUX.2 Klein supports reference images. Install project dependencies with `python3 -m pip install -r requirements.txt`, then make one test keyframe:

```sh
python3 pipeline/generate_keyframes.py --shot shot_02 \
  --reference outputs/keyframes/family_style_reference.png \
  --model @cf/black-forest-labs/flux-2-klein-4b
```

Review that image before generating the remaining shots. Then run the same command without `--shot shot_02` to generate missing keyframes. Existing images are skipped. Use `--overwrite` only when you intentionally want to regenerate existing keyframes. Each API call is recorded in `runs.jsonl`.
