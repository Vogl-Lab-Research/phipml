# Model configuration reference

This reference describes the implemented CLI at phipml **4.2.0**, commit
[`932f14f`](https://github.com/csReynaB/phipml/tree/932f14ffca41ba4f24f3cc570afea27265a5893c).
Start with a complete YAML in `configs/models/`; use this page when adapting it.

## The three parts of a model YAML

| Section | Controls | Example |
|---|---|---|
| Top level | Files, sample IDs, target encoding, feature sources | `metadata_input`, `group_tests`, `transposed` |
| `classification:` | Estimator, cohorts, CV, output paths, decision threshold | `model_type`, `train_filters`, `outer_cv_splits` |
| `param_grid:` | Search spaces for pipeline parameters | `random-forest:`, `xgboost:` |

Use spaces for YAML indentation, native `true`/`false`, `null` for no value, and
lists in brackets or with hyphens. Quoted `"false"` is a string, not a Boolean.
Class and column names must match the input files, including capitalization.

**Path rule:** model YAML paths are relative to the YAML's own directory.
`classification.output_dir` and `input_dir` CLI overrides follow this same rule.
In a plotting YAML, paths are relative to that plotting YAML; explicit plotting
CLI paths are relative to your terminal's current directory. Absolute paths
work in either case.

Explicit model CLI values override the `classification:` section, which
overrides internal defaults. `classification.seed` overrides `random_state`.
Avoid adding unrecognized configuration keys: nested mappings can contain keys
that are not consumed by the CLI.

## Inputs and target: top-level keys

| Key | What to provide and what it means |
|---|---|
| `data_input` | Required path to the peptide matrix, directory of enriched-peptide sample files, or sample-file manifest. In this tutorial: `../../../data/noisy/peptides.csv`. |
| `metadata_input` | Required sample metadata CSV, TSV/TXT, XLSX, or XLS. One row per sample. Must contain the configured sample and target columns. |
| `data_input_mode` | `matrix`, `sample-files`, or `auto`. `auto` treats a directory as sample files and a file as a matrix; explicitly select `sample-files` for a manifest file. |
| `project` | Optional descriptive identifier; output filenames are controlled separately by `classification.output_name`. |
| `col_sample_name` | Sample-ID column in metadata, here `SampleName`. IDs must be unique and match the matrix. The combined matrix's first column is read as its index. |
| `col_target` | Metadata column containing the target classes, here `group_test`. The classification CLI is binary. |
| `group_tests` | Two target labels in encoding order: `[Control, Case]` gives Control=0 and Case=1. Predicted probabilities and positive SHAP direction refer to Case. Non-selected labels are excluded; check that the intended samples remain. |
| `col_predict` | Compatibility column name used by some workflows; default `class1_proba`. This does not change the target or the model's decision threshold. Omitted in the examples. |
| `transposed` | `false` for sample rows × peptide columns; `true` for peptide rows × sample columns. Sample-file mode constructs sample rows automatically. |
| `peptide_prefixes` | Prefixes distinguishing peptides from clinical features. Here `[agilent_, twist_, corona2_]`. A missing trailing underscore is added. All peptide IDs must use your configured prefixes. |
| `extra_features_to_include` | Metadata columns to append, here `[Sex, Smoking, Age, BMI]`; enabled by `classification.with_additional_features`. Do not include target, cohort, participant ID, or outcomes measured after the prediction time. |
| `fillna_value` | Whole-matrix missing-value fill after loading. `null` preserves missingness. A number such as `0` fills both peptide and clinical missingness, so it is not a clinical imputation strategy. |
| `random_state` | General seed; model/CV runs use `classification.seed` if supplied. This does not regenerate synthetic data; the generator has a separate `--data-seed`. |
| `lib_metadata_input` | Peptide annotation file: CSV, TSV/TXT, Excel, or a pandas pickle. Required for library-based peptide filters; also useful for annotated plots. Not required for unfiltered numeric modeling. |
| `lib_col_peptide_name` | Library column identifying peptides, here `peptide_id`. If `null`, table loading uses the first column; pickle input can already use a peptide-ID index. |
| `filters_metadata` | Base sample filter, e.g. `{timepoint: baseline}`. Conditions across keys use AND, a list of allowed values within one key uses OR. Used as the default when no training filter is set. Run-specific training/validation filters replace this mapping when provided, so include required conditions in each cohort filter. |
| `combined_filters_metadata` | List of condition mappings: OR between mappings, AND within each mapping. This stage still applies alongside run-specific cohort filters; keep it `null` for the tutorial. |
| `oligo_filters` | Default peptide-library filter mapping, such as `{Species: Homo sapiens}`. Use annotation columns, not sample metadata. The run can supply its own filters. |
| `oligo_filter_mode` | `all` means AND across library conditions; `any` means OR. Defaults to `all`. |

The loader intersects sample IDs between metadata and the matrix. A typo can
therefore remove samples without meaning that the cohort definition was right.
Check sample counts before fitting and the `Final training data` log message.

### Alternative input: one enrichment file per sample

The main examples use combined matrices. For per-sample enriched-peptide lists,
replace only the data-loading part of your YAML:

```yaml
data_input: ../../../my_data/enriched_samples
data_input_mode: sample-files
sample_file_patterns: ["*.csv"]
sample_file_peptide_column: ID
sample_name_regex: null
```

| Key | Meaning |
|---|---|
| `sample_file_patterns` | Glob patterns within the directory; recursive patterns such as `batch_*/**/*.csv` are supported. |
| `sample_file_peptide_column` | Column containing enriched peptide IDs in every sample file, e.g. `ID`. These are presence lists, not raw sequencing-count matrices. |
| `sample_name_regex` | Optional regex to extract a sample ID from the filename; preferably a named group such as `'prefix_(?P<sample>.+)_enriched'`. `null` uses the filename stem. |

A tab-delimited manifest can list `sample_name` and `path` columns, or one path
per line. Paths in a sample manifest are relative to that manifest. An explicit
sample name takes precedence over the filename-derived name.

## Execution: `classification:` keys

### Model and run type

| Key | Meaning and tutorial value |
|---|---|
| `model_type` | Exactly `random-forest` or `xgboost`; not `random_forest`, `rf`, or `XGB`. |
| `param_grid_name` | Which top-level `param_grid` subsection to read. Keep it equal to `model_type` in these examples. Switching models in a tuned run requires switching this too. |
| `seed` | Estimator/CV/split/bootstrap seed and filename suffix; `420` here. One seed creates one CV run; multiple repeats require multiple commands. |
| `run_nested_cv` | Evaluate the training cohort with outer stratified folds. Each outer model tunes on inner folds if a search space exists; with `param_grid: {}`, this is ordinary outer CV without tuning. |
| `only_train_model` | Fit/save the full-cohort model and stop before external evaluation. If nested CV is enabled, CV runs first. Internal examples set `true`; external examples set `false`. |
| `use_pretrained` | Load a fitted pipeline for full-model external evaluation. It does not stop an independently enabled nested-CV run from fitting fold models. Use `run_nested_cv: false` when only reusing a model. |
| `input_dir` | Directory containing a pretrained artifact, used with `use_pretrained: true`. |
| `input_name` | Direct `.joblib` filename or base name used to find standard saved-model names. An explicit filename is clearest. |
| `output_dir` | Destination for joblib artifacts; created automatically. Give each experiment a separate directory. |
| `output_name` | Base name for `nested_...` and `training_...` artifacts. External artifacts instead use each validation set's `name`. |

### Features and preprocessing

| Key | Meaning and practical effect |
|---|---|
| `with_oligos` | Include peptide features. `true` here. At least this or `with_additional_features` must be true. |
| `with_additional_features` | Include columns in `extra_features_to_include`. `true` here. Adding Sex/Age makes them predictors; it does not by itself establish a causal adjustment. |
| `subgroup` | `all` retains the available library; another column name is a compatibility shortcut for selecting rows where that annotation is true. Use explicit `oligo_filters` for new analyses. |
| `oligo_filters` | Run-specific library filters. Example: `{Species: Homo sapiens, is_PNP: true}`. Use this with `subgroup: all`. Do not combine a named subgroup with non-null filters. |
| `oligo_filter_mode` | `all`/`any` across run-specific annotation conditions. |
| `prevalence_threshold_min` | Minimum percentage of training samples with a nonzero, nonmissing peptide value. Inclusive; tutorial `0`. `1` means 1%, not a proportion of 1. |
| `prevalence_threshold_max` | Maximum percentage with a nonzero, nonmissing peptide value. Inclusive; tutorial `100`. |
| `impute_extra_numeric` | Fit a `SimpleImputer` inside each pipeline for continuous numeric clinical features. Tutorial data are complete, so `false`. It does not impute peptides or numeric binary extras. |
| `extra_numeric_impute_strategy` | `mean`, `median`, `most_frequent`, or `constant`; `median` here. Active only when imputation is enabled. The CLI has no dedicated constant-fill-value option. |
| `fill_missing_peptides_with_zero` | Aligning external data: add absent peptide columns as zero when `true`, otherwise fail. We set `false` because all expected features are measured. Missing clinical columns always fail. This option handles absent columns, not arbitrary NaNs inside present columns. |

The peptide pipeline removes constant columns, then fits an elastic-net
logistic-regression selector. Clinical variables bypass that peptide selector.
Feature selection and optional continuous imputation are fitted inside CV
pipelines. **The current CLI applies prevalence filtering to the full training
cohort before outer CV**, although it excludes external samples. The tutorial
uses 0–100% to make this filter inactive. Do not describe a restricted prevalence
filter as being fitted separately inside every CV fold in this version.

`Sex`/`Gender` values F/Female/M/Male and 0/1 are recognized. Other categorical
clinical variables require numeric encoding before fitting. Define encodings
using training data and apply the same schema externally. Genuine missing
measurements should not automatically become biological absences.

### CV, tuning, and uncertainty

| Key | Meaning and tutorial value |
|---|---|
| `outer_cv_splits` | Number of outer evaluation folds; `3` for the tutorial. Each training sample receives one held-out prediction per run. |
| `inner_cv_splits` | Number of folds used to rank hyperparameter candidates; `2` here. The final full-cohort model uses an additional inner search on the entire training cohort. Ignored for fitting when there is no search. |
| `n_iter` | Number of candidate configurations per Bayesian search, not number of CV repeats or trees. `12` in tuned recipes. It has no tuning effect when `param_grid: {}`. |
| `n_jobs_outer` | Concurrent outer-fold jobs; `1`. |
| `n_jobs_inner` | Concurrent search/CV jobs; `1`. Use a bounded positive number or `-1` for available CPUs. Estimators themselves are created with `n_jobs=1`; avoid multiplying outer and inner parallelism on small machines. |
| `classification_threshold` | Preselected Case-probability cutoff for confusion matrix, accuracy, sensitivity, specificity, F1, etc.; `0.5`. ROC-AUC and AP do not depend on this cutoff. |
| `bootstrap_validation` | Bootstrap the external predictions for uncertainty; `true`. This resamples observations with a fixed fitted model, without refitting or retuning. |
| `bootstrap_n_resamples` | External bootstrap draws; `500` for a short demonstration, implementation default `1000`. More draws reduce Monte Carlo noise, not the uncertainty caused by limited sample size. |
| `bootstrap_confidence_level` | External interval level, as a fraction; `0.95` means 95%. It does not turn CV fold SD into a confidence interval. |

The search score is **average precision** in this commit. It is not a YAML
option. XGBoost's built-in `eval_metric="auc"` does not change the search scorer.
Class stratification preserves class proportions; it does not group repeated
samples from one participant. This CLI has no participant-group CV setting.
The mock data represent independent samples.

For a larger exploratory run, a reasonable starting budget is 5 outer folds,
3 inner folds, and 30 candidates, then repeated seeds if compute permits.
Choose the split design and sample sizes for the scientific study; more repeats
do not create more independent participants. Never select a seed or tuning
recipe by its external-cohort result.

### Cohorts and optional hold-out splitting

| Key | Meaning |
|---|---|
| `train_filters` | Metadata conditions selecting training samples, here `{cohort: training}`. Omitting this from a combined training/external dataset can include external samples in fitting. |
| `validation_sets` | A list of `{name: ..., filters: {...}}` entries, all read from the configured inputs. Names control validation filenames. Example below. |
| `split_filters` | Optional cohort to partition into train and hold-out portions; `null` in the six core examples. |
| `train_size` | Fraction of the split cohort assigned to training; default `0.7`. Active only with `split_filters`. |
| `split_only` | `true` trains/evaluates only the split cohort. With `false`, the split's training portion is appended to `train_filters`, and its held-out portion is appended to each validation set. Use disjoint selections. |

```yaml
classification:
  train_filters: {cohort: training}
  run_nested_cv: false
  only_train_model: false
  validation_sets:
    - name: independent_site
      filters: {cohort: external}
```

Keep participants and any repeated samples disjoint between cohorts. Labeling
rows `external` does not make them independent if they are copied from training.

## What this version supports for external files

At the inspected commit, `validation_sets` accepts `name` and `filters`, not a
separate per-cohort `data_input` or `metadata_input`. The six examples therefore
use a combined matrix and metadata with disjoint training/external IDs. The
training filter excludes external rows from fitting and tuning.

If a new cohort arrives in separate files, combine compatible tables first
(with unique sample IDs, a `cohort` column, and checked feature/metadata schemas)
and then use the filters above. Or adapt the Python API explicitly. The current
pretrained CLI still prepares its training input context, so these reuse recipes
retain the training rows; an external-only CLI workflow is not documented here
as if it were already implemented.

## Useful command overrides

Run these from the tutorial directory:

```bash
# Same noisy dataset, a different CV seed, dedicated output folder.
phipml -c configs/models/random-forest/02_noisy.yaml --seed 421 \
  --output-dir ../../../results/random-forest/repeat_421

# A longer search. Output is kept separate from the reference examples.
phipml -c configs/models/xgboost/03_noisy_tuned.yaml \
  --n-iter 30 --inner-cv-splits 3 --outer-cv-splits 5 \
  --output-dir ../../../results/xgboost/noisy_longer_search

# Untuned clinical-only baseline, on the same target/cohort/CV seed.
phipml -c configs/models/random-forest/02_noisy.yaml \
  --no-with-oligos --with-additional-features \
  --output-name clinical_only --output-dir ../../../results/random-forest/clinical_only

# Untuned peptides-only comparison.
phipml -c configs/models/random-forest/02_noisy.yaml \
  --with-oligos --no-with-additional-features \
  --output-name peptides_only --output-dir ../../../results/random-forest/peptides_only
```

For a tuned estimator change, use the supplied estimator-specific YAML. Merely
passing `--model-type xgboost` to a Random Forest tuning YAML leaves its selected
grid pointing at Random Forest parameters unless it is also replaced.

Source: the pinned repository's
[data/config loader](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/io/data_handler.py),
[run settings](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/classification/train_test_utils.py), and
[training CLI](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/cli/train_test.py).
