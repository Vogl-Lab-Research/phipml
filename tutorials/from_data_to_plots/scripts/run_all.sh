#!/usr/bin/env bash
# Run one estimator (default: random-forest) or both. Logs are retained.
set -euo pipefail
TUTORIAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TUTORIAL_ROOT"
MODE="${1:-random-forest}"
case "$MODE" in
  random-forest|xgboost) MODELS=("$MODE") ;;
  both) MODELS=(random-forest xgboost) ;;
  *) echo "Usage: bash scripts/run_all.sh [random-forest|xgboost|both]" >&2; exit 2 ;;
esac
export MPLBACKEND=Agg
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
for MODEL in "${MODELS[@]}"; do
  mkdir -p "logs/$MODEL"
  for SCENARIO in 01_perfect 02_noisy 03_noisy_tuned 04_external_perfect 05_external_noisy 06_external_noisy_tuned; do
    echo "Running $MODEL / $SCENARIO"
    phipml -c "configs/models/$MODEL/$SCENARIO.yaml" 2>&1 | tee "logs/$MODEL/$SCENARIO.log"
    phipml-plot --plot-config "configs/plots/$MODEL/$SCENARIO.yaml" 2>&1 | tee "logs/$MODEL/${SCENARIO}_plots.log"
  done
  phipml-heatmap --manifest "manifests/$MODEL.csv" --metric roc.auc \
    --vmin 0 --vmax 1 --palette viridis --dpi 180 \
    --title "$MODEL: internal CV and external ROC-AUC" \
    --output "plots/$MODEL/roc_auc_overview"
  phipml-heatmap --manifest "manifests/$MODEL.csv" --metric pr.ap \
    --vmin 0 --vmax 1 --palette viridis --dpi 180 \
    --title "$MODEL: internal CV and external average precision" \
    --output "plots/$MODEL/ap_overview"
done
python scripts/summarize_results.py
