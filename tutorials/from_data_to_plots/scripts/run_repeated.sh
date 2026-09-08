#!/usr/bin/env bash
set -euo pipefail
TUTORIAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TUTORIAL_ROOT"
MODEL="${1:-random-forest}"
case "$MODEL" in random-forest|xgboost) ;; *) echo "Choose random-forest or xgboost" >&2; exit 2 ;; esac
export MPLBACKEND=Agg
mkdir -p "logs/$MODEL/repeated"
# CLI output paths are also resolved relative to the model YAML's directory.
for SEED in 420 421 422; do
  phipml -c "configs/models/$MODEL/02_noisy.yaml" --seed "$SEED" \
    --output-dir "../../../results/$MODEL/repeated_noisy" \
    --no-only-train-model 2>&1 | tee "logs/$MODEL/repeated/$SEED.log"
done
phipml-plot --plot-config "configs/plots/$MODEL/07_repeated_noisy.yaml"
