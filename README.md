# The Gift We Couldn't Guess

A short-film project about our Christmas Eve surprise gift exchange. The storyboard is in `storyboard.json`.

## Quick start

The repository includes the approved storyboard, generated narration, score, keyframes, clips, and final exports. A clean clone can validate the storyboard and rebuild both final MP4s with one command, without provider API keys:

```sh
make film
```

This requires Python 3, `make`, and an FFmpeg build with `subtitles`, `drawtext`, `sidechaincompress`, and `loudnorm` filters. Outputs are written to `outputs/final/original_score/`.

To regenerate production assets from the storyboard, install `requirements.txt`, copy `.env.example` to `.env`, set `GEMINI_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, and `CLOUDFLARE_API_TOKEN`, then run `make regenerate`. The project uses FFmpeg pan-and-zoom in place of GPU video generation. Input hashes let it reuse unchanged keyframes and clips; use `make regenerate FORCE=1` to refresh every image and clip, or `make shot SHOT=shot_03` to regenerate one shot. For a new story, add an instrumental score file and pass its path with `MUSIC=...`; score creation is currently a manual hosted ACE Music step.

### Run in Google Colab

Open [`notebooks/Google_Colab_Run.ipynb`](notebooks/Google_Colab_Run.ipynb) in Colab. `make film` only assembles the committed assets, so it needs no API credentials. To regenerate missing narration or keyframes in Colab, add the Gemini and Cloudflare values to Colab Secrets and follow the notebook's optional regeneration cells. Never paste credentials into a notebook cell or commit them.

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

## Create moving shots without a GPU

The project can use the brief's FFmpeg pan-and-zoom fallback when Kaggle/Colab video generation is unavailable. It creates a nine-second clip per keyframe in both aspect ratios:

```sh
python3 pipeline/generate_panzoom_clips.py
```

Clips are saved under `outputs/clips/16x9/` and `outputs/clips/9x16/`. Existing clips are skipped; use `--overwrite` to regenerate them.

## Assemble a full film draft

After the clips and narration are ready, assemble both formats with English subtitles, narration ducking, and the AI disclosure card:

```sh
python3 pipeline/assemble_film.py
```

To use the selected ACE-Step score and write the exports to a separate folder:

```sh
python3 pipeline/assemble_film.py \
  --music outputs/audio/selected_original_score.mp3 \
  --output-dir outputs/final/original_score
```

The original-score versions are written to `outputs/final/original_score/heritage_short_16x9.mp4` and `outputs/final/original_score/heritage_short_9x16.mp4`. The English subtitle cues follow the storyboard shot timings, so review their synchronization against the Amharic narration during playback.

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
