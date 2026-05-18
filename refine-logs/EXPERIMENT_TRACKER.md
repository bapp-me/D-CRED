# Experiment Tracker

Date: 2026-05-04

Plan: `D:\code\diss_codex\refine-logs\EXPERIMENT_PLAN.md`

## Deployment

- Local GPU detected: NVIDIA GeForce RTX 4060 Laptop GPU.
- Data downloaded:
  - Lending Club granting dataset from Zenodo.
  - UCI Default of Credit Card Clients.
  - Statlog German Credit.
- Main Lending run:
  - Output: `D:\code\diss_codex\D-CRED\outputs\full`
  - Log: `D:\code\diss_codex\D-CRED\logs\full-20260504-002800.out.log`
  - Command used XGBoost CUDA: `--use-gpu-xgb`
- Review-round Lending fix run:
  - Output: `D:\code\diss_codex\D-CRED\outputs\review_round1_fix`
  - Purpose: correct selective review-cost basis and add decision delta CIs.
- Reduced protocol run:
  - Output: `D:\code\diss_codex\D-CRED\outputs\full_reduced`
  - Reduced datasets were run with CPU XGBoost after GPU XGBoost interrupted the small-data reduced stage.

## Block Status

| Block | Status | Artifact |
|---|---:|---|
| B0 Dataset audit | DONE | `outputs/full/feature_audit_lending_club.csv`, `dataset_summary.csv`, `split_summary.csv` |
| B1 Random vs temporal benchmark | DONE | `outputs/full/lending_random_vs_temporal.csv` |
| B2 Calibration | DONE | `outputs/full/calibration_results.csv` |
| B3 Profit/cost decision layer | DONE | `outputs/full/decision_results.csv` |
| B4 Selective decisioning | DONE | `outputs/review_round1_fix/selective_results.csv` |
| B5 UCI/German reduced protocol | DONE | `outputs/full_reduced/reduced_protocol_results.csv`, `reduced_selective_results.csv` |
| B6 Bootstrap CIs | DONE | `outputs/review_round1_fix/bootstrap_ci.csv`, `decision_delta_ci.csv` |

## Key Lending Results

Temporal raw metrics:

| Model | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| LR | 0.6725 | 0.3445 | 0.2221 |
| RF-style LightGBM | 0.6620 | 0.3387 | 0.2207 |
| XGB | 0.6720 | 0.3491 | 0.1621 |

Best temporal calibration by Brier:

| Model | Calibration | ROC-AUC | PR-AUC | Brier | ECE |
|---|---|---:|---:|---:|---:|
| LR | isotonic | 0.6724 | 0.3429 | 0.1598 | 0.0044 |
| RF-style LightGBM | isotonic | 0.6619 | 0.3355 | 0.1610 | 0.0050 |
| XGB | isotonic | 0.6719 | 0.3457 | 0.1597 | 0.0038 |

Cost-sensitive decisioning at FN:FP = 5:1:

| Model | Fixed 0.5 Cost | Cost Threshold Cost | Robust Cost Policy Cost |
|---|---:|---:|---:|
| LR | 1.0656 | 0.6645 | 0.7249 |
| RF-style LightGBM | 1.0797 | 0.6767 | 0.7328 |
| XGB | 1.0753 | 0.6656 | 0.7112 |

Previous split-conformal values from `outputs/full` at alpha=0.10 and review cost multiplier=0.10 used the original false-negative-cost review basis:

| Model | Coverage | Automation | Review | Approved Default Rate | Expected Cost |
|---|---:|---:|---:|---:|---:|
| LR | 0.8984 | 0.0934 | 0.9066 | 0.0647 | 0.4835 |
| RF-style LightGBM | 0.9006 | 0.0779 | 0.9221 | 0.0614 | 0.4850 |
| XGB | 0.8974 | 0.0904 | 0.9096 | 0.0603 | 0.4821 |

Corrected review-round values from `outputs/review_round1_fix`, where review cost is `0.10 * false_positive_cost`:

| Model | Coverage | Automation | Review | Approved Default Rate | Expected Cost |
|---|---:|---:|---:|---:|---:|
| LR | 0.8984 | 0.0934 | 0.9066 | 0.0647 | 0.1209 |
| RF-style LightGBM | 0.9006 | 0.0779 | 0.9221 | 0.0614 | 0.1161 |
| XGB | 0.8974 | 0.0904 | 0.9096 | 0.0603 | 0.1182 |

Paired bootstrap expected-cost deltas on the deterministic 50k test subset show `cost_5_to_1` improves over fixed 0.5, and split conformal improves expected cost under the corrected review-cost convention. The claim remains conservative because split conformal automates only about 8-9% of Lending Club test cases.

Selective-decision interpretation:

- Reviewed cases are modeled as paying review cost only; residual manual-review error is not estimated.
- On Lending Club, split conformal behaves mostly as approve-or-review at the reported operating point: about 91% review, 8-9% automatic approval, and near-zero automatic rejection.

## Implementation Notes

- The default `lr` baseline is `SGDClassifier(loss="log_loss")`, a scalable linear logistic model for the full 1.35M-row sparse design matrix.
- The `rf` label uses LightGBM random-forest mode because sklearn RandomForest hard-exited on the full sparse Lending Club setup.
- RF/XGB fitting uses a stratified 50k training cap for local stability; validation, calibration, testing, decisions, selective review, and CIs use the full split data unless explicitly noted.
- Bootstrap CIs use a deterministic 50k test-observation subset to keep the full run stable in the local background process.
- Validation is reused for calibration, threshold selection, and conformal quantile estimation; this is acceptable for the current MSc experiment but should be stated as a protocol limitation.
- Manual review is modeled optimistically as cost-only; add sensitivity analysis if making stronger deployment claims.
