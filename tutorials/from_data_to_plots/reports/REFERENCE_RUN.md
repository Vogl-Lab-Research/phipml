# Reference execution and observed results

Run date: **8 September 2026**. Source: **phipml 4.2.0**, commit
[`932f14ffca41ba4f24f3cc570afea27265a5893c`](https://github.com/csReynaB/phipml/tree/932f14ffca41ba4f24f3cc570afea27265a5893c).
The upstream source checkout was not modified.

## Environment and budget

The run installed the pinned source into an isolated Linux Python **3.12.13**
environment with the dependency ranges declared in `pyproject.toml`. Main
versions: numpy 1.26.4, pandas 2.2.3, scipy 1.15.3, scikit-learn 1.5.2,
scikit-optimize 0.10.2, XGBoost 2.1.4, SHAP 0.46.0, matplotlib 3.10.9,
and seaborn 0.12.2. The full platform-specific inventory is in
`reports/requirements-reference.txt`; it is distinct from the repository's
Micromamba specification. The Micromamba, Docker, and Apptainer installation
routes were inspected in upstream documentation, not separately executed here.

Data seed **20260908**; model seed **420**. Three outer folds, two inner folds,
12 candidates in each tuned search, one worker at each level, 500 external
bootstrap draws, confidence level 0.95, classification threshold 0.5.

The complete twelve-scenario command, including per-scenario plots, ran in
approximately five minutes on this environment, excluding dependency
installation. This is an observation, not a runtime promise. The model-event
log spans 4 minutes 36 seconds, with the final plot/heatmap/export work afterward.
No outcome-dependent revisions were made to the generated data or tuning space.

## What was run

```bash
python scripts/generate_examples.py
bash scripts/run_all.sh both
bash scripts/run_repeated.sh random-forest
phipml -c configs/models/random-forest/08_reuse_noisy.yaml
phipml -c configs/models/xgboost/08_reuse_noisy.yaml
python scripts/summarize_results.py
```

The main run covers **12 estimator/scenario combinations**, each producing
nine figure types in PDF/SVG/PNG plus the feature table CSV. Both estimator
heatmaps were generated for ROC-AUC and AP. The optional repeated-run example
was executed for Random Forest; the parallel XGBoost repeat recipe is supplied
but was not separately executed. Pretrained model reuse was executed for both.

## Metrics

Internal entries show **mean ± sample SD across outer folds**. External entries
show the point estimate followed by the **95% stratified bootstrap interval**.
These are different uncertainty summaries and should not be read as equivalent
95% intervals. All participants here are synthetic.

| Estimator | Scenario | N evaluated | ROC-AUC | Average precision |
|---|---|---:|---|---|
| random-forest | 01_perfect | 160 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| random-forest | 02_noisy | 160 | 0.912 ± 0.028 | 0.908 ± 0.030 |
| random-forest | 03_noisy_tuned | 160 | 0.911 ± 0.038 | 0.915 ± 0.044 |
| random-forest | 04_external_perfect | 80 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| random-forest | 05_external_noisy | 80 | 0.810 [0.709, 0.898] | 0.843 [0.769, 0.914] |
| random-forest | 06_external_noisy_tuned | 80 | 0.806 [0.705, 0.894] | 0.805 [0.708, 0.900] |
| xgboost | 01_perfect | 160 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| xgboost | 02_noisy | 160 | 0.917 ± 0.038 | 0.921 ± 0.045 |
| xgboost | 03_noisy_tuned | 160 | 0.926 ± 0.030 | 0.928 ± 0.037 |
| xgboost | 04_external_perfect | 80 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| xgboost | 05_external_noisy | 80 | 0.827 [0.728, 0.920] | 0.825 [0.730, 0.931] |
| xgboost | 06_external_noisy_tuned | 80 | 0.808 [0.706, 0.906] | 0.804 [0.707, 0.919] |

Tuning did not improve external AP for either estimator in this run. The
external population has a deliberately weaker signal. These results illustrate
why external data must stay out of model selection; they are not evidence that
tuning is generally unhelpful or that one estimator is superior for real
PhIP-seq data.

The CSV additionally records pooled-score ROC-AUC/AP, accuracy, and F1.
For internal evaluation, pooled-score metrics are not necessarily equal to the
mean of the fold metrics. Prediction CSVs use the pooled sample-level scores.

## Verification performed

- All generated CSVs match their recorded SHA-256 hashes.
- Training and external sample IDs are disjoint in both datasets.
- Every full-cohort artifact contains exactly the 160 intended training labels.
- Every nested artifact covers all 160 intended training samples, with each
  sample assigned to exactly one outer validation fold per run.
- Every external artifact covers exactly the 80 intended external samples.
- Saved labels agree with the input metadata, probabilities are finite/in range,
  and SHAP matrices contain finite values.
- Every core recipe generated all 27 requested figure files and its feature CSV.
- Representative performance, feature-table, and XGBoost SHAP figures were
  visually inspected for legibility and clipping.
- Reusing the saved full-cohort tuned model reproduced scenario 06 predictions
  and SHAP values for both estimators.
- Plotting was exercised from a relocated folder using an explicit local model
  YAML, with deliberately invalid original embedded paths in a temporary test
  artifact. Performance, SHAP beeswarm, and feature-table reconstruction passed.

Detailed checks are recorded in `reports/verification_checks.json`. The normal
training/plotting logs are in `logs/`. The model/config generator, inputs,
search spaces, artifacts, plot recipes, exported predictions, and observed
metrics are included so that the walkthrough can be independently rerun.

## Scope of interpretation

The perfect data intentionally encode their target in engineered predictors.
All annotations are simulated. The noisy scenario is a controlled learning
exercise, not a biological benchmark. The current phipml prevalence filter is
applied before outer CV on the training cohort; it is inactive here at 0–100%.
The current CLI uses sample-level stratified folds, so participant-group
cross-validation would require additional support for repeated-measure studies.

These notes describe observed execution and current limitations; optional
longer-search, clinical-only, and per-sample-file recipes are explanatory
examples rather than additional completed benchmark runs.
