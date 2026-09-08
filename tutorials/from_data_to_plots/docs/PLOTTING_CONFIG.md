# Plot configuration reference

Use **`phipml-plot --plot-config PATH.yaml`** for a saved recipe. Model fitting
and plotting are separate commands: change colors or displayed annotations
without fitting models again. Use `phipml-heatmap` with a CSV/TSV manifest to
compare experiments. This guide describes the current public commands, not the
older plotting modules retained in the repository.

## Start with the right artifact

| Result filename begins with | Content | Plot split |
|---|---|---|
| `nested_` | Outer-fold held-out predictions, SHAP, metrics, fold models | `train` |
| `validation_` | Predictions/SHAP/metrics for an external or explicit hold-out cohort | `test` |
| `training_` | Full-cohort fitted pipeline and input context | Not an evaluation artifact; use it for model reuse, not performance plotting. |

`split: train` is a **storage key** for the training cohort's out-of-fold
evaluation. It does not mean the model is evaluated on samples it just fitted.
For the internal examples the file contains one held-out prediction for each
of the 160 training-cohort samples.

The files embed targets, feature names, SHAP values, metrics, and data-loading
context. They do **not** contain a portable copy of every original input file.
Use `plotting.config` to point to the local model YAML after moving the folder;
the supplied recipes already do this. The original data are still required
for colored feature-value SHAP displays and prevalence/clinical summaries.

## A complete plotting recipe

This example is stored at `configs/plots/random-forest/02_noisy.yaml`.

```yaml
plotting:
  results:
    - ../../../results/random-forest/02_noisy/nested_random-forest_02_noisy_420.joblib
  config: ../../models/random-forest/02_noisy.yaml
  split: train
  plots: [all]
  formats: [pdf, svg, png]
  dpi: 180
  output_dir: ../../../plots/random-forest/02_noisy
  output_prefix: 02_noisy
  title: "random-forest | 02 noisy"
  class_labels: [Control, Case]

  max_display: 10
  feature_ranking: mean-abs-shap
  ranking_top_k: 10
  min_top_k_frequency: 0
  shap_alignment: strict
  save_standalone: true
  reconstruct_data: true

  library_metadata: ../../../data/peptide_library.csv
  library_id_column: peptide_id
  validation_bootstraps: 0
  random_state: 420
  class_colors: ["#386CB0", "#D35D4D"]
  colors:
    roc: "#176B73"
    roc_band: "#B3DAD8"
    pr: "#8A5A44"
    pr_band: "#DFC5B8"
    confusion_cmap: Blues
    classification: "#52796F"
    shap_cmap: phipml_blue_gray_red
    shap_heatmap_cmap: phipml_purple_gray_orange
    shap_importance: "#6D597A"
  feature_table:
    annotation_columns: [Description, Role]
    extra_columns: []
    title: "Synthetic features: model importance and known roles"
    header_color: "#DCE9E9"
    row_colors: ["#F5F8F8", white]
    prevalence_cmap: phipml_prevalence
```

```bash
phipml-plot --plot-config configs/plots/random-forest/02_noisy.yaml
```

The figure files and feature table appear under `plots/random-forest/02_noisy/`.
Relative YAML paths are resolved from the plotting YAML. Explicit CLI paths are
resolved from the current terminal directory, and override YAML values.

## Inputs, output, and figure selection

| `plotting` key | What to provide and what it controls |
|---|---|
| `results` | List of evaluation joblib paths or quoted glob patterns. Multiple files are aggregated as repeated runs; they are not automatically drawn as distinct models in a comparison. |
| `config` | Model YAML for the original input files/labels/annotations. Optional if embedded input paths still resolve; supplied here to make the examples portable. This is different from the command's `--plot-config`. |
| `split` | `train`, `test`, or `auto`. `auto` infers an available evaluation split; explicit values are clearer. |
| `plots` | List drawn from `all`, `performance`, `roc`, `pr`, `confusion`, `classification`, `shap-beeswarm`, `shap-importance`, `shap-heatmap`, `feature-table`. |
| `formats` | One or more of `pdf`, `svg`, `png`. Vector SVG/PDF are useful for editing/sharing; PNG is convenient for slides and previews. |
| `dpi` | Raster resolution; `180` for compact tutorial files. Increase to 300 or 600 if required. This does not change model results or the geometry of vector elements. |
| `output_dir` | Plot destination. If omitted, the CLI considers an explicitly supplied model config's `classification.plot_output_dir`, then its `classification.output_dir/plots`; otherwise it uses `plots/` next to the result. Explicit is easiest. |
| `output_prefix` | Shared output filename stem, e.g. `02_noisy` produces `02_noisy_performance.svg`. Default `phipml`. |
| `title` | Title for the combined performance summary. Some standalone panels have their own labels; do not expect this to rename every panel. |
| `class_labels` | Display labels in `[negative, positive]` order. Defaults to model config labels if available. Relabeling does not change encoded targets. |
| `save_standalone` | `true` saves requested individual ROC/PR/confusion/classification figures. `false` removes those standalone panel requests; include `performance` to retain the combined panel. |
| `reconstruct_data` | `true` loads feature values from explicit/embedded model config. Set false for performance-only plotting without the original data. |
| `validation_bootstraps` | Reconstruct external bootstrap intervals only if missing, for a single `test` artifact with targets available. `0` here because fitting already saved 500-resample intervals. This does not replace existing intervals. |
| `random_state` | Seed for bootstrap reconstruction when used. It does not change predictions or retrain anything. |

### What each plot answers

| `plots` choice | Interpretation | Typical filename suffix |
|---|---|---|
| `performance` | Combined ROC, precision–recall, confusion matrix, and threshold-dependent metric panels. | `_performance` |
| `roc` | Sensitivity versus false-positive rate across score cutoffs. The legend reports ROC-AUC. | `_roc` |
| `pr` | Precision versus recall. The legend reports **AP**, not trapezoidal PR-AUC. Baseline precision depends on positive-class prevalence. | `_pr` |
| `confusion` | Counts of true/false positive/negative predictions at the saved threshold. | `_confusion` |
| `classification` | Metrics such as accuracy, sensitivity, specificity, F1 and MCC at that threshold. | `_classification` |
| `shap-beeswarm` | Distribution of signed contributions per feature; each point represents a sample. Color shows feature value. | `_shap_beeswarm` |
| `shap-importance` | Mean absolute contribution; magnitude without direction. | `_shap_importance` |
| `shap-heatmap` | Patterns of signed contributions across samples and selected features. | `_shap_heatmap` |
| `feature-table` | Compact importance table with class-wise prevalence/clinical summaries and annotations; also exports a detailed CSV. | `_feature_table`, `_feature_importance.csv` |

All nine figure types are generated by `plots: [all]`. The table CSV retains
more features/annotations/audit fields than the compact rendered table.

## Feature ranking and repeated runs

| Key | Meaning |
|---|---|
| `max_display` | Maximum number of ranked features shown in SHAP figures and compact table; `10`. This is a display limit, not model feature selection. |
| `feature_ranking` | `mean-abs-shap` ranks mean absolute SHAP; `top-k-frequency` ranks how often a feature appears in each run's top K. `auto` chooses mean absolute SHAP for one result and top-K frequency for multiple results. |
| `ranking_top_k` | Per-run top-K cutoff used for frequency ranking; `10`. Separate from `max_display`. |
| `min_top_k_frequency` | Minimum percentage of runs whose top K includes a feature; `50` means 50%, not 0.5. Set 0 for the single-file examples. With very few repeats this is only a demonstration of stability. |
| `shap_alignment` | `strict` requires identical sample and feature sets across repeated files, reordered by ID as needed. `intersection` deliberately restricts to shared samples/features and changes the interpreted population. |

Only aggregate runs with the same estimator, data, cohort, feature definition,
class encoding, and threshold. **Do not use a broad glob that mixes Random
Forest, XGBoost, noisy/perfect data, training/external cohorts, or tuned/default
experiments.** Use separate plots or a heatmap manifest for those comparisons.

The repeated plot recipe uses a dedicated `repeated_noisy` folder, and three
seeds on the same dataset. Signed SHAP values are averaged by sample/feature;
ranking/stability statistics also retain run-level absolute importance.
Top-K frequency differs from how often the elastic-net selector retained a
feature. Both statistics can be inspected in the exported CSV.

## Annotations and appearance

| Key | Meaning |
|---|---|
| `library_metadata` | Optional annotation CSV, TSV/TXT, or Excel table used by the plotting CLI. Unlike the model loader, this explicit table reader does not accept pickle. |
| `library_id_column` | Annotation column matching feature IDs; `peptide_id`. Set explicitly to ensure the join uses the right index. |
| `class_colors` | Two colors in `[Control, Case]` order for prediction-direction labels. These do not encode biological class in the SHAP feature-value color scale. |
| `colors.roc`, `colors.roc_band` | ROC curve and uncertainty shading. |
| `colors.pr`, `colors.pr_band` | Precision–recall curve and shading. |
| `colors.confusion_cmap` | Matplotlib colormap for confusion matrix counts. |
| `colors.classification` | Threshold-metric bar color. |
| `colors.shap_cmap` | Feature-value colormap for the beeswarm. |
| `colors.shap_heatmap_cmap` | Diverging colormap for signed SHAP contributions. |
| `colors.shap_importance` | Absolute-SHAP bar color. |
| `feature_table.annotation_columns` | Annotation fields shown in the compact figure, e.g. `[Description, Species, Protein]`. Tutorial uses `[Description, Role]` to distinguish known synthetic signal/noise. |
| `feature_table.extra_columns` | Optional audit columns to display, e.g. `["Top-k SHAP frequency (%)", "Selection frequency (%)"]`. They remain in the CSV when omitted from the figure. |
| `feature_table.title` | Compact-table title. |
| `feature_table.header_color` | Header fill color. |
| `feature_table.row_colors` | Alternating row colors, a two-item list. |
| `feature_table.prevalence_cmap` | Colormap for prevalence cells. |
| `feature_table.input` | Optional curated feature-importance CSV/TSV/Excel. The edited annotations and row order control `feature-table` rendering. Use an exported table as the starting point. |

Quote hex colors because unquoted `#` begins a YAML comment. Use valid
Matplotlib colormaps or the supplied `phipml_blue_gray_red`,
`phipml_purple_gray_orange`, and `phipml_prevalence` maps. Annotation values in
these examples are invented and have no biological meaning.

### Supplying plotting data explicitly

These optional keys are useful for older artifacts or another controlled data
source. They are not needed for the included recipes.

| Key | What to supply |
|---|---|
| `features_table` | Sample-by-feature CSV/TSV/Excel, including `sample_column`. Clinical values must be numeric and use the same encodings as fitting. Include the original feature values, not SHAP values. |
| `target_table` | Table containing sample IDs and the outcome column. Use already encoded 0/1 targets for the explicit table route. |
| `sample_column` | Identifier column for these tables; default `SampleName`. |
| `target_column` | Outcome column in `target_table`, or in `features_table` if no separate target table is supplied. Required with an explicit target table. |
| `feature_importance_table` | Top-level alternative to `feature_table.input`. Use the exported CSV structure, including its `Feature` column. |

Saved sample IDs determine alignment. The supplied model-config reconstruction
route also checks reconstructed labels against saved targets. This check cannot
prove all feature measurements are unchanged; preserve input data and hashes.

## Common plotting commands

From the tutorial root:

```bash
# Change appearance/format without retraining.
phipml-plot --plot-config configs/plots/random-forest/02_noisy.yaml \
  --formats svg png --dpi 300 --max-display 8 \
  --output-dir plots/custom_noisy --output-prefix presentation

# Only performance panels; original feature data are not required.
phipml-plot results/random-forest/02_noisy/nested_random-forest_02_noisy_420.joblib \
  --split train --plots performance --no-reconstruct-data \
  --class-labels Control Case --output-dir plots/performance_only

# External model evaluation.
phipml-plot --plot-config configs/plots/xgboost/06_external_noisy_tuned.yaml

# Regenerate a compact table after manually editing a COPY of its exported CSV.
phipml-plot --plot-config configs/plots/random-forest/02_noisy.yaml \
  --plots feature-table \
  --feature-importance-table plots/random-forest/02_noisy/02_noisy_feature_importance.csv \
  --output-dir plots/curated_table --max-display 8
```

Editing a feature table changes presentation; it does not revise SHAP values or
model predictions. Display a curated subset transparently.

## Comparison heatmaps

`phipml-heatmap` takes a **manifest**, not a plotting YAML. Each row identifies
an evaluation artifact:

```csv
training,validation,path,split
RF noisy default,Internal CV,../results/random-forest/02_noisy/nested_random-forest_02_noisy_420.joblib,train
RF noisy default,External,../results/random-forest/05_external_noisy/validation_random-forest_05_external_noisy_420.joblib,test
```

The path is relative to the manifest file. The `training` value labels a heatmap
column and `validation` labels a row; labels can describe experiment conditions
as in the supplied manifests. Multiple rows for one cell are aggregated as
repeated run estimates. Use explicit files, not globs, in the manifest.

```bash
phipml-heatmap --manifest manifests/random-forest.csv \
  --metric roc.auc --palette viridis --vmin 0 --vmax 1 --dpi 180 \
  --title "Random Forest: internal and external performance" \
  --output plots/random-forest/roc_auc_overview

phipml-heatmap --manifest manifests/xgboost.csv \
  --metric pr.ap --palette viridis --vmin 0 --vmax 1 --dpi 180 \
  --output plots/xgboost/ap_overview
```

| Heatmap argument | Meaning |
|---|---|
| `--manifest` | Required CSV/TSV/TXT with `training`, `validation`, `path`, and optional `split`. |
| `--metric` | Dotted metric key, e.g. `roc.auc`, `pr.ap`, `classification.f1`, `classification.balanced_accuracy`, or `classification.mcc`. |
| `--training-order` | Optional ordered list of column labels; must include all manifest training labels. |
| `--validation-order` | Optional ordered list of row labels. |
| `--order` | Legacy shared order for a square matrix; do not combine with the two independent orders. Usually unnecessary. |
| `--title` | Figure title. |
| `--palette` | Matplotlib/seaborn colormap name; `viridis` here. |
| `--vmin`, `--vmax` | Color-scale bounds. Use 0–1 for this overview, −1–1 for MCC. The CLI defaults are 0.5–1.0, which can obscure below-0.5 values. |
| `--output` | Required filename stem; requested format extensions are added/replaced. |
| `--formats` | One or more of `pdf svg png`; defaults to all three. |
| `--dpi` | Raster resolution. |
| `--annotate-uncertainty` / `--no-annotate-uncertainty` | Show/hide available native intervals or variability. Default shows them. |

The rectangular overview uses only conditions that exist. An internal-CV cell
and an external cell summarize different evaluation procedures; their numbers
are not a paired statistical test.

## Interpreting uncertainty and SHAP honestly

| Evaluation | Displayed uncertainty | What it describes |
|---|---|---|
| One nested-CV artifact | Across-outer-fold variability; curve bands are mean ±1 sample SD. | Sensitivity to the fold partition. It is not a formal 95% confidence interval. |
| Multiple seed artifacts | 2.5–97.5% empirical interval across run estimates. | Variation across repeated fits on reused participants; not independent-cohort confidence. |
| One external artifact with bootstrap | Class-stratified paired bootstrap interval at the requested confidence level. | Sampling variability of the external observations conditional on the fitted model; it excludes refitting/tuning uncertainty. |

The perfect synthetic scenario can have a 1.0–1.0 bootstrap interval because
every resampled set remains perfectly separated. This is a property of the
constructed demonstration, not evidence that a clinical model has no uncertainty.

Positive SHAP contributions move the model output toward the positive class;
negative values move it away. Random Forest tree SHAP is in its probability
output scale here, while XGBoost's default tree SHAP explains the raw margin
(log-odds for the binary logistic objective). Do not compare their numerical
SHAP magnitudes directly or describe XGBoost values as probability-point
changes. SHAP describes a fitted predictive relationship, not causation or a
p-value. Correlated engineered peptides may share importance unevenly, and
independent noise can acquire apparent importance in a finite sample.

Source: the pinned repository's
[plot CLI](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/cli/plot_results.py),
[result aggregation](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/plots/result_summary.py), and
[heatmap CLI](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/cli/metric_heatmap.py).
