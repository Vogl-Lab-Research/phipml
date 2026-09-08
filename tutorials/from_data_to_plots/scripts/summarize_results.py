#!/usr/bin/env python3
"""Export observed metrics, sample predictions, and selected pipeline settings."""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows, parameters = [], []
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    prediction_dir = out / "predictions"
    prediction_dir.mkdir(exist_ok=True)
    for model in ("random-forest", "xgboost"):
        for path in sorted((ROOT / "results" / model).glob("*/*.joblib")):
            if path.name.startswith("training_"):
                result = joblib.load(path)
                params = result["best_estimator"].get_params(deep=True)
                parameters.append({"model": model, "scenario": path.parent.name, "seed": path.stem.rsplit("_", 1)[1],
                                   "parameters": {k: v for k, v in params.items() if k.startswith("estimator__") or k.startswith("preprocessor__peptides__feature_selection__estimator__")}})
                continue
            if not path.name.startswith(("nested_", "validation_")):
                continue
            result = joblib.load(path)
            split = "train" if path.name.startswith("nested_") else "test"
            metrics = result[f"metrics_{split}"]
            y, scores = result[f"target_{split}"], result[f"scores_{split}"]
            scores = scores.reindex(y.index)
            if scores.isna().any() or y.index.has_duplicates:
                raise ValueError(f"Incomplete predictions or duplicate sample IDs: {path}")
            row = {"model": model, "scenario": path.parent.name, "seed": path.stem.rsplit("_", 1)[1],
                   "evaluation": "outer CV" if split == "train" else "external", "n": len(y),
                   "roc_auc": metrics["roc"]["auc"], "average_precision": metrics["pr"]["ap"],
                   "accuracy": metrics["classification"]["accuracy"], "f1": metrics["classification"]["f1"],
                   "roc_auc_fold_sd": metrics["roc"].get("auc_std"), "ap_fold_sd": metrics["pr"].get("ap_std"),
                   "roc_auc_ci_lower": metrics["roc"].get("auc_ci_lower"), "roc_auc_ci_upper": metrics["roc"].get("auc_ci_upper"),
                   "ap_ci_lower": metrics["pr"].get("ap_ci_lower"), "ap_ci_upper": metrics["pr"].get("ap_ci_upper"),
                   "pooled_score_auc": roc_auc_score(y, scores), "pooled_score_ap": average_precision_score(y, scores),
                   "path": str(path.relative_to(ROOT))}
            rows.append(row)
            pd.DataFrame({"SampleName": y.index, "target": y.to_numpy(), "class1_probability": scores.to_numpy(),
                          "predicted_class": (scores.to_numpy() >= 0.5).astype(int)}).to_csv(prediction_dir / f"{model}_{path.parent.name}_{row['seed']}.csv", index=False)
    if not rows:
        raise SystemExit("No result files found. Run a model first.")
    table = pd.DataFrame(rows)
    table.to_csv(out / "observed_metrics.csv", index=False)
    (out / "fitted_parameters.json").write_text(json.dumps(parameters, indent=2, default=str) + "\n")
    print(table[["model", "scenario", "seed", "n", "roc_auc", "average_precision"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("Wrote reports/observed_metrics.csv, predictions/, and fitted_parameters.json")


if __name__ == "__main__":
    main()
