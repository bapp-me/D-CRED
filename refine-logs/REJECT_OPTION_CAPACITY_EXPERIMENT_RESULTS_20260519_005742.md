# Initial Reject-Option Capacity Results

Date: 20260519-005640
Output directory: `D:\code\diss_codex\D-CRED\outputs\reject_capacity_full`

## Primary Calibrated Source

- Model: `lgbm`
- Calibration: `sigmoid`
- Selected on: `calibration_select` by Brier, ECE, then NLL.

## Top Calibration Candidates On Calibration-Select

| model | calibration | brier | ece | nll | roc_auc | pr_auc |
| --- | --- | --- | --- | --- | --- | --- |
| lgbm | sigmoid | 0.179453 | 0.0516815 | 0.539984 | 0.667735 | 0.393224 |
| xgb | sigmoid | 0.179462 | 0.0518261 | 0.540039 | 0.66761 | 0.393754 |
| lgbm | isotonic | 0.179481 | 0.0518205 | 0.540214 | 0.66753 | 0.388998 |
| xgb | isotonic | 0.179486 | 0.0518616 | 0.540125 | 0.66739 | 0.388527 |
| lr | isotonic | 0.180282 | 0.0506959 | 0.542436 | 0.661109 | 0.381299 |

## Primary Scenario Final-Test Policies

| policy | capacity_fraction | expected_cost | realized_cost | review_rate | automation_rate | savings_vs_no_review | savings_vs_all_review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no_review_cost_sensitive |  | 0.621649 | 0.620791 | 0 | 1 | 0 | -0.459485 |
| all_review |  | 0.162165 | 0.162165 | 1 | 0 | 0.459485 | 0 |
| cost_aware_reject_option |  | 0.161971 | 0.162149 | 0.990977 | 0.00902278 | 0.459679 | 0.000194004 |
| capacity_aware_deferral | 0.01 | 0.615167 | 0.614088 | 0.00998739 | 0.990013 | 0.00648238 | -0.453002 |
| capacity_aware_deferral | 0.02 | 0.608695 | 0.607207 | 0.0199896 | 0.98001 | 0.0129548 | -0.44653 |
| capacity_aware_deferral | 0.05 | 0.58939 | 0.588111 | 0.0499963 | 0.950004 | 0.0322593 | -0.427225 |
| capacity_aware_deferral | 0.1 | 0.557621 | 0.555421 | 0.0999926 | 0.900007 | 0.064028 | -0.395457 |
| capacity_aware_deferral | 0.2 | 0.495667 | 0.492598 | 0.2 | 0.8 | 0.125983 | -0.333502 |
| capacity_aware_deferral | 0.3 | 0.436145 | 0.432649 | 0.299993 | 0.700007 | 0.185504 | -0.273981 |
| capacity_aware_deferral | 0.5 | 0.326083 | 0.322157 | 0.499993 | 0.500007 | 0.295566 | -0.163918 |
| uncertainty_band |  | 0.522622 | 0.521404 | 0.159249 | 0.840751 | 0.0990278 | -0.360457 |
| uncertainty_band |  | 0.398836 | 0.39928 | 0.386154 | 0.613846 | 0.222813 | -0.236671 |
| uncertainty_band |  | 0.26395 | 0.27058 | 0.710395 | 0.289605 | 0.357699 | -0.101785 |
| split_conformal |  | 0.311052 | 0.302503 | 0.543415 | 0.456585 | 0.310597 | -0.148888 |
| split_conformal |  | 0.353593 | 0.343918 | 0.473859 | 0.526141 | 0.268057 | -0.191428 |
| split_conformal |  | 0.353593 | 0.343918 | 0.473859 | 0.526141 | 0.268057 | -0.191428 |
| empirical_conformal_risk_control |  | 0.166451 | 0.168596 | 0.933279 | 0.0667211 | 0.455198 | -0.00428646 |
| empirical_conformal_risk_control |  | 0.168339 | 0.170249 | 0.920665 | 0.0793352 | 0.45331 | -0.00617411 |

## Capacity Frontier

| policy | capacity_fraction | expected_cost | review_rate | savings_vs_no_review |
| --- | --- | --- | --- | --- |
| no_review_cost_sensitive |  | 0.621649 | 0 | 0 |
| all_review |  | 0.162165 | 1 | 0.459485 |
| cost_aware_reject_option |  | 0.161971 | 0.990977 | 0.459679 |
| capacity_aware_deferral | 0.01 | 0.615167 | 0.00998739 | 0.00648238 |
| capacity_aware_deferral | 0.02 | 0.608695 | 0.0199896 | 0.0129548 |
| capacity_aware_deferral | 0.05 | 0.58939 | 0.0499963 | 0.0322593 |
| capacity_aware_deferral | 0.1 | 0.557621 | 0.0999926 | 0.064028 |
| capacity_aware_deferral | 0.2 | 0.495667 | 0.2 | 0.125983 |
| capacity_aware_deferral | 0.3 | 0.436145 | 0.299993 | 0.185504 |
| capacity_aware_deferral | 0.5 | 0.326083 | 0.499993 | 0.295566 |

## Status

- M0 protocol split and selection protocol: DONE.
- M1/M2 calibrated PD source: DONE for configured models.
- M3/M4 reject-option and capacity-aware deferral: DONE for selected source.
- M5 conformal risk-control: empirical variant only; do not claim formal finite-sample guarantee.