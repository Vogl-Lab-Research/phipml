#!/usr/bin/env python3
"""Create deterministic synthetic data and phipml 4.2.0 YAML recipes.

Run from any directory. Outputs live beside this script's parent directory.
No real participant data and no phipml source-code changes are involved.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "932f14ffca41ba4f24f3cc570afea27265a5893c"
SCENARIOS = [
    "01_perfect", "02_noisy", "03_noisy_tuned",
    "04_external_perfect", "05_external_noisy", "06_external_noisy_tuned",
]
MODELS = ["random-forest", "xgboost"]


def dump_yaml(path: Path, value: dict, comment: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(comment + "\n" + yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def search_space(model: str) -> dict:
    shared = {
        "preprocessor__peptides__feature_selection__estimator__l1_ratio":
            {"type": "real", "low": 0.2, "high": 0.8},
        "preprocessor__peptides__feature_selection__estimator__C":
            {"type": "real", "low": 0.1, "high": 10.0, "prior": "log-uniform"},
    }
    if model == "random-forest":
        specific = {
            "estimator__n_estimators": {"type": "integer", "low": 60, "high": 160},
            "estimator__max_depth": {"type": "integer", "low": 2, "high": 10},
            "estimator__min_samples_split": {"type": "integer", "low": 2, "high": 10},
            "estimator__min_samples_leaf": {"type": "integer", "low": 1, "high": 6},
            "estimator__max_features": {"type": "categorical", "categories": ["sqrt", "log2", 0.5]},
            "estimator__class_weight": {"type": "categorical", "categories": [None, "balanced"]},
        }
    else:
        specific = {
            "estimator__n_estimators": {"type": "integer", "low": 50, "high": 160},
            "estimator__learning_rate": {"type": "real", "low": 0.02, "high": 0.25, "prior": "log-uniform"},
            "estimator__max_depth": {"type": "integer", "low": 2, "high": 5},
            "estimator__min_child_weight": {"type": "integer", "low": 1, "high": 8},
            "estimator__subsample": {"type": "real", "low": 0.65, "high": 1.0},
            "estimator__colsample_bytree": {"type": "real", "low": 0.65, "high": 1.0},
            "estimator__reg_lambda": {"type": "real", "low": 0.1, "high": 10.0, "prior": "log-uniform"},
            "estimator__reg_alpha": {"type": "real", "low": 0.0001, "high": 1.0, "prior": "log-uniform"},
            "estimator__gamma": {"type": "real", "low": 0.0, "high": 2.0},
        }
    return {model: {**shared, **specific}}


def model_config(model: str, scenario: str, n_iter: int) -> dict:
    signal = "perfect" if "perfect" in scenario else "noisy"
    external = "external" in scenario
    tuned = "tuned" in scenario
    return {
        "project": f"tutorial_{scenario}",
        "data_input": f"../../../data/{signal}/peptides.csv",
        "metadata_input": f"../../../data/{signal}/metadata.csv",
        "data_input_mode": "matrix",
        "lib_metadata_input": "../../../data/peptide_library.csv",
        "lib_col_peptide_name": "peptide_id",
        "col_sample_name": "SampleName",
        "col_target": "group_test",
        "group_tests": ["Control", "Case"],
        "transposed": False,
        "peptide_prefixes": ["agilent_", "twist_", "corona2_"],
        "extra_features_to_include": ["Sex", "Smoking", "Age", "BMI"],
        "fillna_value": None,
        "filters_metadata": None,
        "combined_filters_metadata": None,
        "random_state": 420,
        "classification": {
            "model_type": model,
            "param_grid_name": model,
            "seed": 420,
            "run_nested_cv": not external,
            "use_pretrained": False,
            "only_train_model": not external,
            "with_oligos": True,
            "with_additional_features": True,
            "subgroup": "all",
            "oligo_filters": None,
            "oligo_filter_mode": "all",
            "prevalence_threshold_min": 0,
            "prevalence_threshold_max": 100,
            "outer_cv_splits": 3,
            "inner_cv_splits": 2,
            "n_iter": n_iter if tuned else 1,
            "n_jobs_outer": 1,
            "n_jobs_inner": 1,
            "impute_extra_numeric": False,
            "extra_numeric_impute_strategy": "median",
            "fill_missing_peptides_with_zero": False,
            "classification_threshold": 0.5,
            "bootstrap_validation": True,
            "bootstrap_n_resamples": 500,
            "bootstrap_confidence_level": 0.95,
            "train_filters": {"cohort": "training"},
            "split_filters": None,
            "split_only": False,
            "validation_sets": [{"name": scenario, "filters": {"cohort": "external"}}] if external else [],
            "output_dir": f"../../../results/{model}/{scenario}",
            "output_name": scenario,
        },
        "param_grid": search_space(model) if tuned else {},
    }


def plot_config(model: str, scenario: str, *, repeated: bool = False) -> dict:
    external = "external" in scenario
    kind = "validation" if external else "nested"
    folder = "repeated_noisy" if repeated else scenario
    source = f"../../../results/{model}/{folder}/{kind}_{model}_{scenario}_{'*' if repeated else '420'}.joblib"
    return {"plotting": {
        "results": [source],
        "config": f"../../models/{model}/{scenario}.yaml",
        "split": "test" if external else "train",
        "plots": ["all"],
        "formats": ["pdf", "svg", "png"],
        "dpi": 180,
        "output_dir": f"../../../plots/{model}/{folder}",
        "output_prefix": folder,
        "title": f"{model} | {folder.replace('_', ' ')}",
        "class_labels": ["Control", "Case"],
        "max_display": 10,
        "feature_ranking": "top-k-frequency" if repeated else "mean-abs-shap",
        "ranking_top_k": 10,
        "min_top_k_frequency": 50 if repeated else 0,
        "shap_alignment": "strict",
        "save_standalone": True,
        "reconstruct_data": True,
        "library_metadata": "../../../data/peptide_library.csv",
        "library_id_column": "peptide_id",
        "validation_bootstraps": 0,
        "random_state": 420,
        "class_colors": ["#386CB0", "#D35D4D"],
        "colors": {
            "roc": "#176B73", "roc_band": "#B3DAD8",
            "pr": "#8A5A44", "pr_band": "#DFC5B8",
            "confusion_cmap": "Blues", "classification": "#52796F",
            "shap_cmap": "phipml_blue_gray_red",
            "shap_heatmap_cmap": "phipml_purple_gray_orange",
            "shap_importance": "#6D597A",
        },
        "feature_table": {
            "annotation_columns": ["Description", "Role"],
            "extra_columns": [],
            "title": "Synthetic features: model importance and known roles",
            "header_color": "#DCE9E9",
            "row_colors": ["#F5F8F8", "white"],
            "prevalence_cmap": "phipml_prevalence",
        },
    }}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-seed", type=int, default=20260908)
    parser.add_argument("--n-iter", type=int, default=12)
    args = parser.parse_args()
    if args.n_iter < 1:
        parser.error("--n-iter must be positive")
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    names = ["agilent_signal_01", "twist_signal_02", "corona2_signal_03",
             "agilent_signal_04", "twist_signal_05", "corona2_signal_06"]
    names += [f"{['agilent', 'twist', 'corona2'][i % 3]}_noise_{i:03d}" for i in range(1, 75)]
    library = pd.DataFrame({
        "peptide_id": names,
        "Description": [f"Synthetic signal {i+1}" for i in range(6)] + [f"Noise peptide {i}" for i in range(1, 75)],
        "Role": ["engineered signal"] * 6 + ["independent noise"] * 74,
        "Species": ["Simulated organism"] * 80,
        "Protein": [f"Synthetic protein {i // 2 + 1}" for i in range(80)],
        "is_demo_signal": [True] * 6 + [False] * 74,
    })
    library.to_csv(ROOT / "data/peptide_library.csv", index=False)
    for signal_index, signal in enumerate(["perfect", "noisy"]):
        folder = ROOT / "data" / signal
        folder.mkdir(parents=True, exist_ok=True)
        matrices, metadata = [], []
        rates = np.random.default_rng(args.data_seed + 900).uniform(0.10, 0.55, 74)
        for cohort_index, (cohort, n) in enumerate([("training", 160), ("external", 80)]):
            rng = np.random.default_rng(np.random.SeedSequence([args.data_seed, signal_index, cohort_index]))
            y = np.repeat([0, 1], n // 2)
            rng.shuffle(y)
            sample_ids = [f"{signal}_{cohort}_{i:03d}" for i in range(1, n + 1)]
            if signal == "perfect":
                engineered = np.column_stack([y, 1-y, y, 1-y, y, 1-y])
            else:
                # Prespecified mild distribution shift: weaker signal externally.
                strength = 0.70 if cohort == "training" else 0.65
                p = np.where(y == 1, strength, 1-strength)
                engineered = np.column_stack([rng.binomial(1, p if j % 2 == 0 else 1-p) for j in range(6)])
            noise = rng.binomial(1, rates, size=(n, 74))
            frame = pd.DataFrame(np.column_stack([engineered, noise]), index=sample_ids, columns=names)
            frame.index.name = "SampleName"
            matrices.append(frame)
            metadata.append(pd.DataFrame({
                "SampleName": sample_ids, "group_test": np.where(y == 1, "Case", "Control"),
                "cohort": cohort, "Sex": rng.choice(["Female", "Male"], n),
                "Smoking": rng.binomial(1, 0.25, n),
                "Age": np.round(rng.normal(50 + 4*cohort_index, 10, n), 1),
                "BMI": np.round(rng.normal(25, 3, n), 1),
            }))
        combined = pd.concat(matrices)
        combined.to_csv(folder / "peptides.csv")
        pd.concat(metadata, ignore_index=True).to_csv(folder / "metadata.csv", index=False)
        combined.T.rename_axis("peptide_id").to_csv(folder / "peptides_transposed.csv")
    manifest_rows = []
    for model in MODELS:
        for scenario in SCENARIOS:
            cfg = model_config(model, scenario, args.n_iter)
            dump_yaml(ROOT / "configs/models" / model / f"{scenario}.yaml", cfg,
                      "# phipml 4.2.0 tutorial. Paths are relative to this YAML.\n# See docs/MODEL_CONFIG.md and docs/HYPERPARAMETERS.md for every setting.")
            dump_yaml(ROOT / "configs/plots" / model / f"{scenario}.yaml", plot_config(model, scenario),
                      "# Run: phipml-plot --plot-config <this-file>\n# Explicit model config makes input paths portable after extraction.")
            ext = "external" in scenario
            condition = "Perfect / default" if "perfect" in scenario else ("Noisy / tuned" if "tuned" in scenario else "Noisy / default")
            manifest_rows.append({
                "training": f"{'RF' if model == 'random-forest' else 'XGB'} | {condition}",
                "validation": "External" if ext else "Internal CV",
                "path": f"../results/{model}/{scenario}/{'validation' if ext else 'nested'}_{model}_{scenario}_420.joblib",
                "split": "test" if ext else "train",
            })
        dump_yaml(ROOT / "configs/plots" / model / "07_repeated_noisy.yaml",
                  plot_config(model, "02_noisy", repeated=True), "# Three repeat seeds are produced by scripts/run_repeated.sh.")
        reused = model_config(model, "06_external_noisy_tuned", args.n_iter)
        reused["classification"].update({
            "use_pretrained": True,
            "input_dir": f"../../../results/{model}/03_noisy_tuned",
            "input_name": f"training_{model}_03_noisy_tuned_420.joblib",
            "output_dir": f"../../../results/{model}/08_reuse_noisy",
            "validation_sets": [{"name": "08_reuse_noisy", "filters": {"cohort": "external"}}],
        })
        reused["param_grid"] = {}
        dump_yaml(ROOT / "configs/models" / model / "08_reuse_noisy.yaml", reused,
                  "# Run 03_noisy_tuned first. Load that fixed full-cohort model; do not refit.")
    (ROOT / "manifests").mkdir(exist_ok=True)
    pd.DataFrame(manifest_rows).to_csv(ROOT / "manifests/all_results.csv", index=False)
    for model, label in [("random-forest", "RF"), ("xgboost", "XGB")]:
        pd.DataFrame([r for r in manifest_rows if r["training"].startswith(label + " |")]).to_csv(
            ROOT / f"manifests/{model}.csv", index=False)
    fingerprints = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((ROOT / "data").rglob("*.csv"))}
    spec = {
        "phipml_commit": COMMIT, "data_seed": args.data_seed, "model_seed": 420,
        "n_training": 160, "n_external": 80, "n_peptides": 80, "n_extras": 4,
        "class_balance": "50% Control / 50% Case within each cohort",
        "perfect": "Six target/inverse-target synthetic peptides; 74 independent noise peptides.",
        "noisy": "Six independent conditional Bernoulli signals: 0.70 vs 0.30 training; 0.65 vs 0.35 external. Alternating signs.",
        "clinical": "Sex, Smoking, Age, BMI independent of class; external Age shifted +4 years.",
        "tuning": "Identical noisy data and model seeds for default/tuned pairs. No selection based on external outcomes.",
        "n_iter_tuned": args.n_iter, "sha256": fingerprints,
    }
    (ROOT / "data/generation_manifest.json").write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Created 2 datasets, 12 scenario configs, 2 reuse configs, 14 plot configs in {ROOT}")


if __name__ == "__main__":
    main()
