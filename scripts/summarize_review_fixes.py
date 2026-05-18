from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize D-CRED review-round evidence into stable review-stage artifacts."
    )
    parser.add_argument("--lending-dir", required=True, type=Path)
    parser.add_argument("--reduced-dir", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("review-stage"), type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    lending_summary = summarize_lending(args.lending_dir, args.output_dir)
    reduced_summary = summarize_reduced(args.reduced_dir, args.output_dir)
    write_claim_summary(args.output_dir / "ROUND1_FIX_SUMMARY.md", lending_summary, reduced_summary)


def summarize_lending(lending_dir: Path, output_dir: Path) -> dict[str, object]:
    random_temporal = pd.read_csv(lending_dir / "lending_random_vs_temporal.csv")
    calibration = pd.read_csv(lending_dir / "calibration_results.csv")
    decisions = pd.read_csv(lending_dir / "decision_results.csv")
    selective = pd.read_csv(lending_dir / "selective_results.csv")
    delta_ci_path = lending_dir / "decision_delta_ci.csv"
    delta_ci = pd.read_csv(delta_ci_path) if delta_ci_path.exists() else pd.DataFrame()

    best_calibration = (
        calibration[calibration["split"].eq("temporal")]
        .sort_values(["model", "brier"])
        .groupby("model", as_index=False)
        .head(1)
        .loc[:, ["model", "calibration", "roc_auc", "pr_auc", "brier", "ece", "nll"]]
    )
    best_calibration.to_csv(output_dir / "lending_best_temporal_calibration.csv", index=False)

    decision_5 = decisions[
        decisions["split"].eq("temporal") & decisions["scenario"].eq("cost_fn_5_fp_1")
    ].copy()
    fixed = decision_5[decision_5["policy"].eq("fixed_0.5")].set_index("model")
    cost5 = decision_5[decision_5["policy"].eq("cost_5_to_1")].set_index("model")
    robust = decision_5[decision_5["policy"].eq("robust_cost")].set_index("model")
    rows = []
    for model in sorted(set(fixed.index) & set(cost5.index)):
        rows.append(
            {
                "model": model,
                "fixed_0.5_cost": fixed.loc[model, "expected_cost"],
                "cost_5_to_1_cost": cost5.loc[model, "expected_cost"],
                "cost_5_to_1_delta": cost5.loc[model, "expected_cost"]
                - fixed.loc[model, "expected_cost"],
                "cost_5_to_1_approval_rate": cost5.loc[model, "approval_rate"],
                "cost_5_to_1_approved_default_rate": cost5.loc[
                    model, "approved_default_rate"
                ],
                "robust_cost": robust.loc[model, "expected_cost"],
                "robust_approval_rate": robust.loc[model, "approval_rate"],
                "robust_approved_default_rate": robust.loc[
                    model, "approved_default_rate"
                ],
            }
        )
    lending_delta = pd.DataFrame(rows)

    conformal = selective[
        selective["split"].eq("temporal")
        & selective["method"].eq("split_conformal")
        & selective["alpha"].eq(0.10)
        & selective["review_cost_multiplier"].eq(0.10)
    ].copy()
    conformal = conformal.set_index("model")
    for col in [
        "coverage",
        "automation_rate",
        "review_rate",
        "approved_default_rate",
        "expected_cost",
    ]:
        lending_delta[f"split_conformal_{col}"] = lending_delta["model"].map(conformal[col])
    lending_delta.to_csv(output_dir / "lending_decision_delta_summary.csv", index=False)
    if not delta_ci.empty:
        delta_ci.to_csv(output_dir / "lending_decision_delta_ci.csv", index=False)

    random_temporal.to_csv(output_dir / "lending_random_temporal_summary.csv", index=False)

    return {
        "lending_dir": str(lending_dir),
        "random_temporal": random_temporal,
        "best_calibration": best_calibration,
        "decision_delta": lending_delta,
        "delta_ci": delta_ci,
    }


def summarize_reduced(reduced_dir: Path, output_dir: Path) -> dict[str, object]:
    protocol = pd.read_csv(reduced_dir / "reduced_protocol_results.csv")
    selective = pd.read_csv(reduced_dir / "reduced_selective_results.csv")

    metric_rows = protocol[protocol["roc_auc"].notna()].copy()
    calibration_summary = (
        metric_rows.groupby(["dataset", "model", "calibration"], as_index=False)
        .agg(
            roc_auc_mean=("roc_auc", "mean"),
            roc_auc_std=("roc_auc", "std"),
            pr_auc_mean=("pr_auc", "mean"),
            pr_auc_std=("pr_auc", "std"),
            brier_mean=("brier", "mean"),
            brier_std=("brier", "std"),
            ece_mean=("ece", "mean"),
            ece_std=("ece", "std"),
        )
        .sort_values(["dataset", "model", "brier_mean"])
    )
    calibration_summary.to_csv(output_dir / "reduced_calibration_summary.csv", index=False)

    cost_rows = protocol[protocol["scenario"].eq("cost_fn_5_fp_1")].copy()
    cost_summary = (
        cost_rows.groupby(["dataset", "model", "policy"], as_index=False)
        .agg(
            expected_cost_mean=("expected_cost", "mean"),
            expected_cost_std=("expected_cost", "std"),
            approval_rate_mean=("approval_rate", "mean"),
            approved_default_rate_mean=("approved_default_rate", "mean"),
        )
        .sort_values(["dataset", "model", "expected_cost_mean"])
    )
    cost_summary.to_csv(output_dir / "reduced_cost_summary.csv", index=False)

    selective_summary = (
        selective.groupby(
            ["dataset", "model", "method", "alpha", "band", "review_cost_multiplier"],
            dropna=False,
            as_index=False,
        )
        .agg(
            coverage_mean=("coverage", "mean"),
            automation_rate_mean=("automation_rate", "mean"),
            review_rate_mean=("review_rate", "mean"),
            approved_default_rate_mean=("approved_default_rate", "mean"),
            expected_cost_mean=("expected_cost", "mean"),
        )
        .sort_values(["dataset", "model", "method", "expected_cost_mean"])
    )
    selective_summary.to_csv(output_dir / "reduced_selective_summary.csv", index=False)

    return {
        "reduced_dir": str(reduced_dir),
        "calibration_summary": calibration_summary,
        "cost_summary": cost_summary,
        "selective_summary": selective_summary,
    }


def write_claim_summary(
    path: Path,
    lending: dict[str, object],
    reduced: dict[str, object],
) -> None:
    rt = lending["random_temporal"]
    decision = lending["decision_delta"]
    conformal_cost = decision[
        ["model", "split_conformal_expected_cost", "split_conformal_automation_rate", "split_conformal_review_rate"]
    ]
    reduced_cost = reduced["cost_summary"]
    best_reduced = reduced_cost.groupby(["dataset", "model"], as_index=False).head(1)

    lines = [
        "# Round 1 Fix Summary",
        "",
        "## Claim-Control Summary",
        "",
        "- C1 is narrowed: temporal evaluation changes the deployment environment; it is not framed as uniformly worse than random split.",
        "- C2 is supported: calibration changes Brier/ECE and can differ from ranking metrics.",
        "- C3 is supported: cost-aware thresholds reduce expected cost versus fixed 0.5 on Lending Club.",
        "- C4 is narrowed: split conformal is a conservative review-heavy control layer, not a high-automation deployment win.",
        "- C5 is partial: UCI/German are reduced-protocol sanity checks, summarized across three seeds with no temporal claim.",
        "",
        "## Limitations To Carry Into The Dissertation",
        "",
        "- RF is a LightGBM random-forest surrogate and RF/XGB fit on a stratified 50k training cap.",
        "- Validation data are reused for calibration, threshold selection, and conformal quantile estimation.",
        "- Bootstrap CIs use a deterministic 50k test-observation subset for local stability.",
        "- Reduced-protocol UCI/German results use three seeds and should be treated as sanity checks.",
        "- The feature audit is a curated application-time protocol for the granting dataset, not a raw-feature contamination stress test.",
        "",
        "## Lending Random vs Temporal",
        "",
        markdown_table(rt),
        "",
        "## Lending Cost And Selective Decision Summary",
        "",
        markdown_table(decision),
        "",
        "## Split-Conformal Operating Point",
        "",
        markdown_table(conformal_cost),
        "",
        "## Reduced-Protocol Best Cost Policies",
        "",
        markdown_table(
            best_reduced[
                [
                    "dataset",
                    "model",
                    "policy",
                    "expected_cost_mean",
                    "approval_rate_mean",
                    "approved_default_rate_mean",
                ]
            ]
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    try:
        return frame.to_markdown(index=False)
    except ImportError:
        return "```\n" + frame.to_string(index=False) + "\n```"


if __name__ == "__main__":
    main()
