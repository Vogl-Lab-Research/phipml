# What the hyperparameters mean

phipml fits a pipeline: peptide preprocessing/selection, optional clinical
imputation, then a Random Forest or XGBoost classifier. A **hyperparameter** is
a setting chosen before fitting; training then estimates model coefficients or
trees from the training samples. The tuned examples choose hyperparameters by
inner cross-validation, using **average precision (AP)**.

These are small teaching search spaces, not claimed optimal settings for
PhIP-seq. The same noisy data, target, cohort filters, and seed are used for
untuned/tuned pairs. Better training or inner-CV performance does not guarantee
better outer-CV or external performance.

## Read a parameter path

```yaml
param_grid:
  random-forest:
    estimator__max_depth:
      type: integer
      low: 2
      high: 10
```

`classification.param_grid_name: random-forest` selects this section.
`estimator__max_depth` means “the `max_depth` parameter of the pipeline step
called `estimator`.” Double underscores traverse nested pipeline objects.

The longer path
`preprocessor__peptides__feature_selection__estimator__C` changes the **logistic
regression used to select peptides**, not the final Random Forest/XGBoost.

| Search specification | Meaning | Valid example |
|---|---|---|
| `type: integer` | Whole-number choices between inclusive bounds | `{type: integer, low: 2, high: 10}` |
| `type: real` | Continuous values between bounds | `{type: real, low: 0.2, high: 0.8}` |
| `type: categorical` | Choose one of the listed alternatives | `{type: categorical, categories: [sqrt, log2, 0.5]}` |
| `prior: uniform` | Equal weight to equal-width intervals; default for reals | Useful for a fraction such as `subsample`. |
| `prior: log-uniform` | Equal weight across multiplicative scales | Useful for `C`, learning rate, or regularization; both bounds must be strictly positive. |

Do not use equal `low`/`high` to hold a value fixed. Use a one-element categorical
space, e.g. `{type: categorical, categories: [100]}`. This still invokes the
search machinery if `param_grid` is nonempty. The current CLI does not expose a
separate `estimator_params` block for fixed overrides. `param_grid: {}` uses
the built-in pipeline and estimator defaults; it does not disable feature
selection.

## Shared peptide selector

Both models fit elastic-net logistic regression with `solver: saga`, then retain
peptides whose absolute coefficient meets the selection threshold.

| Full parameter key | Tutorial search | Meaning | Effect of increasing it |
|---|---|---|---|
| `preprocessor__peptides__feature_selection__estimator__l1_ratio` | 0.2–0.8, uniform | Mix of L1 and L2 penalties: 0=pure L2, 1=pure L1. Fixed default 0.5. | Generally promotes sparser selection as the L1 share increases, though correlated predictors can change which peptide survives. |
| `preprocessor__peptides__feature_selection__estimator__C` | 0.1–10, log-uniform | Inverse regularization strength. Fixed default 1.0. | Weaker shrinkage, often more selected peptides; a small value may eliminate nearly all peptide signal. |

Fixed implementation settings are `VarianceThreshold(threshold=0.0)`, selector
`threshold=1e-5`, and logistic-regression `max_iter=10000`. The selector is
supervised and learns from class labels inside the fitted CV pipeline. Clinical
features do not pass through this peptide selector. Inactive peptide search
parameters are ignored when no peptide branch exists.

Feature selection can choose different peptides in different folds. The saved
SHAP matrices retain original feature names and assign zero to unused features
for the relevant fitted model/fold. A zero SHAP value is not proof of no
biological association.

## Random Forest

A Random Forest averages many randomized decision trees. Each tree can capture
nonlinear patterns; averaging reduces the sensitivity to any one fitted tree.

Use the exact final-model prefix `estimator__` for every parameter below.

| Parameter key | Tutorial search | Meaning | Practical tradeoff |
|---|---|---|---|
| `estimator__n_estimators` | Integer 60–160 | Number of trees. Untuned sklearn default: 100. | More trees usually stabilize predictions, but cost time/memory; tree count alone does not control overfitting as strongly as tree size. |
| `estimator__max_depth` | Integer 2–10 | Maximum depth of each tree. Untuned default: `None` (no explicit depth limit). | Deeper trees fit finer interactions and noise; shallow trees may underfit. |
| `estimator__min_samples_split` | Integer 2–10 | Minimum observations required in a node before attempting a split. Untuned default: 2. | Larger values suppress splits on small groups. This is different from the size of each resulting leaf. |
| `estimator__min_samples_leaf` | Integer 1–6 | Minimum observations in each terminal leaf. Untuned default: 1. | Larger leaves smooth predicted probabilities and reduce small-sample fitting. |
| `estimator__max_features` | `sqrt`, `log2`, or `0.5` | Number/fraction of available features considered at a split, after preprocessing. Untuned default: `sqrt`. | Smaller subsets decorrelate trees, but can hide useful features at a split. `0.5` is numeric: half of available features, not the string `"0.5"`. |
| `estimator__class_weight` | `null` or `balanced` | Weight the contribution of classes to fitting. Untuned default: `None`. | `balanced` weights inversely to class frequency. It can change decision behavior; it does not rebalance the evaluation cohort. |

Other supported Random Forest parameters can be added through a valid pipeline
search path. Common optional choices:

| Parameter | How to specify | Meaning |
|---|---|---|
| `estimator__bootstrap` | `{type: categorical, categories: [true, false]}` | Whether each tree uses a bootstrap sample. Default `true`. |
| `estimator__criterion` | `{type: categorical, categories: [gini, entropy]}` | Criterion for scoring candidate splits; default `gini`. |
| `estimator__class_weight` | Add `balanced_subsample` to categories | Recalculate inverse-frequency weights separately for each tree's bootstrap sample. |

The balanced mock classes are included to keep the demonstration easy to read;
class weighting is present to teach its meaning, not because imbalance needs
correction in these data.

## XGBoost

XGBoost builds trees sequentially. Each boosting round adds a correction to the
current model. Smaller learning steps often need more trees. The phipml factory
sets `objective="binary:logistic"`, `tree_method="hist"`, `eval_metric="auc"`,
`n_jobs=1`, and the configured seed. Other untuned settings come from the
installed XGBoost version. There is no early-stopping evaluation set supplied
by this CLI.

| Parameter key | Tutorial search | Meaning | Practical tradeoff |
|---|---|---|---|
| `estimator__n_estimators` | Integer 50–160 | Maximum number of boosting rounds/trees for this tree booster. | More rounds add capacity; combine with `learning_rate`. Without early stopping, the configured rounds are fitted. |
| `estimator__learning_rate` | 0.02–0.25, log-uniform | Shrinkage applied to each added tree; also called eta. | Smaller steps often need more rounds and can improve generalization; too few rounds then underfit. |
| `estimator__max_depth` | Integer 2–5 | Maximum depth of a tree. | Larger values fit more complex interactions and require more data/memory. |
| `estimator__min_child_weight` | Integer 1–8 | Minimum sum of second-order loss weights (Hessians) required in a child node. | Larger values discourage splits. This is **not** a literal minimum sample count for logistic classification. |
| `estimator__subsample` | 0.65–1.0, uniform | Fraction of training observations used in each boosting iteration. | Values below 1 introduce row subsampling; too little data per round can weaken learning. |
| `estimator__colsample_bytree` | 0.65–1.0, uniform | Fraction of available features sampled for each tree. | Can reduce correlated tree behavior and fitting to noise; may miss useful predictors. |
| `estimator__reg_lambda` | 0.1–10, log-uniform | L2 regularization on leaf weights. | Larger values shrink leaf contributions and make the model more conservative. |
| `estimator__reg_alpha` | 0.0001–1.0, log-uniform | L1 regularization on leaf weights. | Larger values can set some leaf contributions to zero. The positive lower bound makes the log-uniform prior valid. |
| `estimator__gamma` | 0–2, uniform | Minimum reduction in objective required to accept a split. | Larger values discourage low-benefit splits. |

Optional `estimator__scale_pos_weight` increases the training weight assigned to
the positive class. If exploring it, use training-fold information and validate
its effect. It is omitted here because the synthetic classes are balanced.
Do not add `class_weight` to an XGBoost grid or `learning_rate` to a Random
Forest grid.

## How tuning is evaluated

For `03_noisy_tuned`:

1. Split the training cohort into three outer folds.
2. For each outer fold, run 12 candidate configurations using two inner folds
   on the outer-training subset; refit the best candidate on that subset.
3. Predict and explain the held-out outer subset exactly once.
4. Combine the outer-fold results into the nested artifact.
5. Run a fresh inner search on all 160 training samples and save the resulting
   full-cohort pipeline for reuse.

This costs approximately `3 × (12 × 2 + 1) + (12 × 2 + 1) = 100` pipeline fits.
It is a teaching budget for a fairly wide space. `BayesSearchCV` in the pinned
scikit-optimize version starts with 10 initialization candidates by default;
12 candidates allow a short adaptive phase. A two-candidate smoke run exercises
the search workflow but cannot demonstrate a mature Bayesian optimization.

For `06_external_noisy_tuned`, there is one inner search on the full training
cohort, followed by evaluation of its fixed selected model on 80 external
samples. External labels do not choose parameters, features, or thresholds.

Inspect what was actually chosen:

```bash
python scripts/summarize_results.py
```

Open `reports/fitted_parameters.json` for full-cohort pipeline settings, or:

```python
from pathlib import Path
import joblib

path = Path("results/random-forest/03_noisy_tuned/training_random-forest_03_noisy_tuned_420.joblib")
model = joblib.load(path)["best_estimator"]
print(model.named_steps["estimator"].get_params())
selector = model.named_steps["preprocessor"].named_transformers_["peptides"].named_steps["feature_selection"]
print(selector.estimator_.get_params())
```

Outer-fold selected settings can differ from this full-cohort model; they are
available from `model_list` in the nested artifact. The CLI saves the chosen
models, not the complete `BayesSearchCV.cv_results_` optimization history.

Implementation source:
[pipeline, selector and search](https://github.com/csReynaB/phipml/blob/932f14ffca41ba4f24f3cc570afea27265a5893c/src/phipml/classification/helpers.py).
Parameter semantics were checked against the installed scikit-learn 1.5.2 and
XGBoost 2.1.4 classes used for the reference run. Further reference:
[RandomForestClassifier](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.RandomForestClassifier.html),
[LogisticRegression](https://scikit-learn.org/1.5/modules/generated/sklearn.linear_model.LogisticRegression.html),
[XGBoost parameters](https://xgboost.readthedocs.io/en/release_2.1.0/parameter.html).
