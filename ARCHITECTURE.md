# Pipeline architecture

## Contract and flow

`storyboard.json` is the project contract. `schema/storyboard.schema.json` defines the required film metadata and shot fields; `pipeline/validate_storyboard.py` checks schema validity, unique shot IDs, and a 60–90 second runtime.

```text
storyboard.json
  ├─ generate_narration.py ──> outputs/audio/narration_<content-hash>.wav
  ├─ generate_keyframes.py ──> outputs/keyframes/<shot-id>.jpg
  ├─ generate_panzoom_clips.py ──> outputs/clips/{16x9,9x16}/<shot-id>.mp4
  └─ assemble_film.py + narration + score + clips
       └─ outputs/final/original_score/{heritage_short_16x9,heritage_short_9x16}.mp4
```

`make film` validates the storyboard and assembles both formats from the generated inputs stored in the repository. It needs Python, FFmpeg with `subtitles`, `drawtext`, `sidechaincompress`, and `loudnorm` filters, and the chosen score file. It does not call external APIs.

`make regenerate` runs the narration, keyframe, pan-and-zoom, and assembly scripts in sequence. New narration or keyframes require Gemini and Cloudflare credentials in a local `.env`; the selected score is a provided input because ACE Music has no generation API in this project. `make shot SHOT=shot_03` regenerates that keyframe and its two pan-and-zoom clips, then reassembles the film.

## Cache and rerun behavior

- Narration is content-addressed by the Amharic transcript, TTS model, voice, and style; an unchanged request reuses its WAV.
- `outputs/cache_manifest.json` stores input and output hashes for keyframes and clips. A changed image prompt/style/reference/model invalidates that shot's keyframe; the changed keyframe hash then invalidates that shot's two motion clips. Unchanged shots are reused. Use `make regenerate FORCE=1` to refresh all images/clips or `make shot SHOT=<id>` to force one shot.
- Every external API call and every local pan-and-zoom render is appended to `runs.jsonl` with stage, provider/model, parameters, status, and latency where measurable. Provider-reported cost is not available in every entry; see `COSTS.md`.

## Failure handling and limits

- Kaggle remained in session startup, so the project uses the brief's FFmpeg pan-and-zoom fallback. These are moving stills, not generated character animation.
- The score was generated separately with the ACE Music hosted interface and saved as `outputs/audio/selected_original_score.mp3`.
- Cloud API failures are logged and stop that generation stage. The scripts do not implement automatic retries; rerun after correcting the reported error.
- English subtitle timing follows shot boundaries rather than word-level timestamps.
- `notebooks/Google_Colab_Run.ipynb` documents the Colab route for cloning the repository, installing FFmpeg, and assembling or regenerating the film.
