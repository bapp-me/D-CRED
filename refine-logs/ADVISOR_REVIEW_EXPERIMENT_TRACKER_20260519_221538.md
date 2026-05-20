# Advisor Review Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| A001 | M0 | Parse supervisor review | Review triage | Current D-CRED | protocol risks | MUST | DONE | Main ask is month-blocked seven-role rerun. |
| A002 | M0 | Parse dean review | Review triage | Current D-CRED | economic realism risks | MUST | DONE | True cash-flow direction identified but blocked by local CSV schema. |
| A003 | M0 | Check current Lending Club fields | Data audit | `data/raw/LC_loans_granting_model_dataset.csv` | header fields | MUST | DONE | Dataset has granting features only; no repayment cash-flow columns. |
| M101 | M1 | Implement month-blocked role split | `temporal_month_blocked_role_split` | Lending Club | no shared month | MUST | DONE | Added `--role-split-mode month`. |
| M102 | M1 | Run small month-blocked sanity | LR sanity | 20k rows | split feasibility | SHOULD | DONE | Failed as expected because first 20k rows contain only one issue month. |
| M103 | M1 | Run full month-blocked LR sanity | LR | full Lending | output smoke | MUST | DONE | `outputs/reject_capacity_month_blocked_lr/` completed. |
| M104 | M1 | Add selected-only final-test mode | CLI/protocol | full Lending | final metric rows | MUST | DONE | `--selected-only-final-test` writes only selected-source final metrics. |
| M201 | M2 | Full month-blocked reject-capacity rerun | LR/LGBM/XGB | full Lending | Brier/ECE/NLL, decision costs | MUST | DONE | `outputs/reject_capacity_month_blocked/` completed. |
| M202 | M2 | Month boundary audit | Audit CSV | full Lending | `n_roles` by month | MUST | DONE | 139/139 months are `OK_NO_SHARED_MONTH`. |
| M203 | M2 | Verify selected source | LGBM/sigmoid | calibration_select | Brier/ECE/NLL | MUST | DONE | Same selected source as row-wise main run. |
| M204 | M2 | Verify capacity frontier | Capacity-aware deferral | final_test | expected cost vs capacity | MUST | DONE | Expected cost decreases monotonically from 1% to 50% review capacity. |
| M301 | M3 | Compare row-wise vs month-blocked | Result comparison | final_test | cost deltas | MUST | DONE | `ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv` written. |
| E001 | M4 | Implement feature-acquisition pilot | New script | full Lending | parseable outputs | MUST | DONE | `scripts/economic_feature_acquisition_pilot.py` added. |
| E101 | M4 | Train cheap-feature PD model | SGD logistic | month roles | proxy utility decisions | MUST | DONE | Cheap model simulates initial screen. |
| E102 | M4 | Train full-feature PD model | SGD logistic | month roles | proxy utility decisions | MUST | DONE | Full model simulates acquired review information. |
| E201 | M4 | Train VOI scorer | SGD regressor | policy_tune | predicted utility gain | MUST | DONE | Scores expected full-vs-cheap utility value from cheap features. |
| E301 | M4 | Run feature-acquisition frontier | Random/uncertainty/VOI/oracle | final_test | expected/realized proxy utility | MUST | DONE | `outputs/economic_feature_acquisition_pilot/feature_acquisition_frontier.csv` written. |
| E901 | M5 | True loan-level cash-flow experiment | Cash-flow utility | external accepted-loan data | observed profit/loss | SHOULD | BLOCKED | Requires fields absent from the local granting dataset. |
