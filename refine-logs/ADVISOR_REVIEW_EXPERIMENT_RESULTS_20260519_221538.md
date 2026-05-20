# Advisor Review Experiment Results

**Date**: 2026-05-19

**Plan**: `refine-logs/ADVISOR_REVIEW_EXPERIMENT_PLAN.md`

## Results By Milestone

### M0: Review Triage - PASSED

- Supervisor advice maps to one high-priority repair: strict month-blocked role splitting and rerun of the existing reject-capacity pipeline.
- Dean advice maps to a larger research direction: observed cash-flow utility plus budgeted feature acquisition.
- The current local Lending Club granting CSV does not contain the repayment cash-flow fields needed for the full dean direction. Available columns are application/granting fields plus `Default`.

### M1: Month-Blocked Split Implementation - PASSED

- Added `temporal_month_blocked_role_split` and CLI support via `--role-split-mode month`.
- Added `month_boundary_audit.csv`.
- Added `--selected-only-final-test` so the new frozen run writes final-test metrics only for the selected calibrated source.
- Small 20k-row month sanity failed because the first 20k CSV rows contain only one `issue_d` month; this is a data-ordering property, not a code failure. Full-data sanity passed.

### M2: Month-Blocked Reject-Capacity Rerun - PASSED

Output directory: `outputs/reject_capacity_month_blocked/`

Month boundary audit:

| Status | Count |
|---|---:|
| OK_NO_SHARED_MONTH | 139 |

Month-blocked role split:

| Partition | Rows | Default Rate | Start Month | End Month | Issue Months |
|---|---:|---:|---|---|---:|
| model_train | 689303 | 0.1814 | 2007-06 | 2015-08 | 99 |
| model_dev | 101043 | 0.1970 | 2015-09 | 2015-11 | 3 |
| calibration_fit | 150921 | 0.2049 | 2015-12 | 2016-03 | 4 |
| calibration_select | 142777 | 0.2522 | 2016-04 | 2016-10 | 7 |
| policy_tune | 129674 | 0.2372 | 2016-11 | 2017-06 | 8 |
| risk_calibration | 67758 | 0.2308 | 2017-07 | 2017-11 | 5 |
| final_test | 66205 | 0.1660 | 2017-12 | 2018-12 | 13 |

Selected calibrated source:

- Month-blocked selected source: `lgbm/sigmoid`.
- Row-wise selected source from the previous main run: `lgbm/sigmoid`.
- Month-blocked final-test selected-source metrics: Brier `0.130503`, ECE `0.010674`, NLL `0.421082`, ROC-AUC `0.680730`, PR-AUC `0.289666`.
- Previous row-wise final-test selected-source metrics: Brier `0.131047`, ECE `0.010752`, NLL `0.422521`, ROC-AUC `0.680174`, PR-AUC `0.290553`.

Primary scenario final-test frontier under month blocking:

| Policy | Capacity | Expected Cost | Review Rate | Savings vs No Review |
|---|---:|---:|---:|---:|
| no_review_cost_sensitive |  | 0.619721 | 0.0000 | 0.000000 |
| all_review |  | 0.161972 | 1.0000 | 0.457749 |
| cost_aware_reject_option |  | 0.161807 | 0.9917 | 0.457914 |
| capacity_aware_deferral | 0.01 | 0.613231 | 0.0100 | 0.006490 |
| capacity_aware_deferral | 0.02 | 0.606758 | 0.0200 | 0.012963 |
| capacity_aware_deferral | 0.05 | 0.587459 | 0.0500 | 0.032262 |
| capacity_aware_deferral | 0.10 | 0.555700 | 0.1000 | 0.064021 |
| capacity_aware_deferral | 0.20 | 0.493793 | 0.2000 | 0.125928 |
| capacity_aware_deferral | 0.30 | 0.434348 | 0.3000 | 0.185373 |
| capacity_aware_deferral | 0.50 | 0.324600 | 0.5000 | 0.295121 |

Interpretation:

- The supervisor's month-blocked robustness concern is resolved for the main capacity-frontier claim.
- The main qualitative story is stable: selected source does not change; the capacity frontier remains monotone; unrestricted reject option still degenerates to near all-review.
- The thesis should say "robust to stricter month-blocked temporal isolation" for the capacity-frontier direction, not "all-review is beaten in a practical sense."

### M3: Row-Wise vs Month-Blocked Comparison - PASSED

Comparison file: `refine-logs/ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv`

Key deltas:

- No-review expected cost: row-wise `0.621649`, month-blocked `0.619721`, delta `-0.001929`.
- All-review expected cost: row-wise `0.162165`, month-blocked `0.161972`, delta `-0.000193`.
- Unrestricted reject-option expected cost: row-wise `0.161971`, month-blocked `0.161807`, delta `-0.000164`.
- Capacity-aware 5% expected cost: row-wise `0.589390`, month-blocked `0.587459`, delta `-0.001931`.
- Capacity-aware 10% expected cost: row-wise `0.557621`, month-blocked `0.555700`, delta `-0.001921`.
- Capacity-aware 50% expected cost: row-wise `0.326083`, month-blocked `0.324600`, delta `-0.001483`.

The month-blocked run is slightly better numerically on expected cost, but the important result is stability, not improvement.

### M4: Proxy Economic Utility And Feature Acquisition Pilot - COMPLETED WITH CAVEATS

Output directory: `outputs/economic_feature_acquisition_pilot/`

Scope guardrail:

- Current data lacks `total_pymnt`, `total_rec_int`, `recoveries`, `collection_recovery_fee`, and similar observed repayment cash-flow fields.
- This pilot uses `loan_amnt`, ROI `0.10`, LGD `0.60`, and review/acquisition cost `$10` as proxy utility.
- This is not final observed bank economics.

Proxy utility distribution on final test:

| Quantity | Count | Mean | Median | P25 | P75 | P95 |
|---|---:|---:|---:|---:|---:|---:|
| signed_proxy_cash | 66205 | -497.453 | 1000 | 380 | 1800 | 3500 |
| non_default_profit_if_approved | 55214 | 1443.83 | 1200 | 650 | 2000 | 3500 |
| default_loss_if_approved | 10991 | 10249.6 | 9000 | 5760 | 15000 | 21000 |

Feature-acquisition frontier excerpt:

| Policy | Capacity | Expected Utility | Realized Utility | Review Rate | Utility Lift vs No Review | Lift per Review Dollar |
|---|---:|---:|---:|---:|---:|---:|
| no_review_cheap_model |  | 4.9583 | 2.3909 | 0.0000 |  |  |
| all_review_full_model |  | 1.2970 | 13.8571 | 1.0000 | -3.6613 | -0.3661 |
| uncertainty_review | 0.05 | 6.6332 | 9.7333 | 0.0500 | 1.6749 | 3.3501 |
| predicted_value_of_information | 0.05 | 6.5837 | 9.4226 | 0.0500 | 1.6255 | 3.2512 |
| uncertainty_review | 0.10 | 7.3160 | 12.9622 | 0.1000 | 2.3577 | 2.3579 |
| predicted_value_of_information | 0.10 | 7.2118 | 11.7541 | 0.1000 | 2.2535 | 2.2537 |
| uncertainty_review | 0.20 | 7.7301 | 16.6261 | 0.2000 | 2.7718 | 1.3859 |
| predicted_value_of_information | 0.20 | 7.5077 | 14.3846 | 0.1700 | 2.5494 | 1.4994 |
| uncertainty_review | 0.50 | 6.0889 | 18.4395 | 0.5000 | 1.1306 | 0.2261 |
| predicted_value_of_information | 0.50 | 7.5077 | 14.3846 | 0.1700 | 2.5494 | 1.4994 |

Interpretation:

- The pilot proves the dean's two-stage information acquisition path is implementable in this repo.
- It does not prove the new predicted VOI method is superior: in this proxy setting, uncertainty review is slightly better at 5%, 10%, and 20% capacity. Predicted VOI stops at about 17% review because no additional cases have positive predicted net value under the $10 acquisition cost.
- The oracle VOI upper bound is much higher, which suggests the bottleneck is predicting value of information from cheap features, not the absence of review value.
- This should be written as a scoped pilot or future-work bridge, not as a new main thesis result unless richer cash-flow data are added.

## Summary

- 4/4 must-run supervisor robustness items completed.
- 1/1 scoped dean feature-acquisition pilot completed.
- True dean-level observed cash-flow utility remains blocked by dataset schema.
- Main result: month-blocked robustness supports the current D-CRED capacity-frontier narrative with stronger temporal isolation.
- Ready for thesis integration: YES, with the proxy-utility caveat preserved.

## Next Step

Update the dissertation results/protocol text to make `outputs/reject_capacity_month_blocked/` the strict temporal robustness evidence. Keep `outputs/economic_feature_acquisition_pilot/` as appendix or future-work evidence unless a true accepted-loan cash-flow dataset is added.
