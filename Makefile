PYTHON ?= python3
MUSIC ?= outputs/audio/selected_original_score.mp3
REFERENCE ?= outputs/keyframes/family_style_reference.png
MODEL ?= @cf/black-forest-labs/flux-2-klein-4b
OUTPUT_DIR ?= outputs/final/original_score
OVERWRITE ?=
SHOT ?=

NARRATION_PATH := $(shell set -a; [ ! -f .env ] || . ./.env; set +a; $(PYTHON) pipeline/generate_narration.py --print-output-path 2>/dev/null)

.PHONY: help validate film regenerate shot

help:
	@echo "make film                 Assemble both formats from the checked-in assets (no API key needed)."
	@echo "make regenerate           Generate missing stages, then assemble; requires API keys if outputs are missing."
	@echo "make regenerate FORCE=1   Regenerate all keyframes and pan/zoom clips."
	@echo "make shot SHOT=shot_03    Regenerate one keyframe and its two clips, then reassemble."
	@echo "Set MUSIC=path/to/score.mp3 to use another instrumental score."

validate:
	$(PYTHON) pipeline/validate_storyboard.py

film: validate
	$(PYTHON) pipeline/assemble_film.py --narration "$(NARRATION_PATH)" --music "$(MUSIC)" --output-dir "$(OUTPUT_DIR)"

regenerate: validate
	@test -f .env || (echo "Create .env from .env.example before regenerating API assets." >&2; exit 2)
	@set -a; . ./.env; set +a; $(PYTHON) pipeline/generate_narration.py
	@set -a; . ./.env; set +a; $(PYTHON) pipeline/generate_keyframes.py --reference "$(REFERENCE)" --model "$(MODEL)" $(if $(FORCE),--overwrite,)
	$(PYTHON) pipeline/generate_panzoom_clips.py $(if $(FORCE),--overwrite,)
	$(PYTHON) pipeline/assemble_film.py --narration "$(NARRATION_PATH)" --music "$(MUSIC)" --output-dir "$(OUTPUT_DIR)"

shot: validate
	@test -n "$(SHOT)" || (echo "Usage: make shot SHOT=shot_03" >&2; exit 2)
	@test -f .env || (echo "Create .env from .env.example before regenerating API assets." >&2; exit 2)
	@set -a; . ./.env; set +a; $(PYTHON) pipeline/generate_narration.py
	@set -a; . ./.env; set +a; $(PYTHON) pipeline/generate_keyframes.py --shot "$(SHOT)" --overwrite --reference "$(REFERENCE)" --model "$(MODEL)"
	$(PYTHON) pipeline/generate_panzoom_clips.py --shot "$(SHOT)" --overwrite
	$(PYTHON) pipeline/assemble_film.py --narration "$(NARRATION_PATH)" --music "$(MUSIC)" --output-dir "$(OUTPUT_DIR)"
