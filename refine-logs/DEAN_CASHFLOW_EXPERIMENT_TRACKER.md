# Dean Cash-Flow Experiment Tracker

Updated: 2026-05-20 00:25

Primary run: `outputs/dean_cashflow_full`

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| C001 | M0 | Verify `loan.csv` schema | Data audit | full raw file | required fields | MUST | DONE | Cash-flow columns are present: `funded_amnt`, `total_rec_prncp`, `total_rec_int`, `total_rec_late_fee`, `recoveries`, `collection_recovery_fee`. |
| C002 | M0 | Build terminal accepted-loan sample | Data prep | terminal statuses | rows, status mix | MUST | DONE | Terminal sample has 1,306,387 rows; censored Current/Late/In Grace rows excluded. |
| C003 | M0 | Construct `net_cash` outcome | Cash-flow labels | terminal loans | profit/loss distribution | MUST | DONE | Cash-flow fields are outcomes only and are not predictors; `funded_amnt` predictor contradiction fixed and rerun completed. |
| C004 | M0 | Build month-blocked roles | Split protocol | terminal loans | no shared month | MUST | DONE | Final test is 2017-11 through 2018-12, 67,461 rows; month audit has no shared month. |
| C101 | M1 | Train cheap PD/cash models | Cheap features | model_train | AUC, Brier, cash error | MUST | DONE | Final-test cheap PD AUC 0.6460; Brier 0.2358; cash MAE 4067.2. |
| C102 | M1 | Train full PD/cash models | Full review features | model_train | AUC, Brier, cash error | MUST | DONE | Final-test full PD AUC 0.6768; Brier 0.2132; cash MAE 3795.6. Some all-missing full numeric fields were skipped by sklearn. |
| C103 | M1 | Economic utility policies | Fixed/tuned/cash | final_test | realized utility | MUST | DONE | Tuned cash model is best among direct policies at -25.96 per application, versus tuned PD -109.12 and fixed PD -524.14. |
| C201 | M2 | Fit VOI scorer | `g(x_cheap)` | policy_tune | downstream utility | MUST | DONE | Predicted-VOI scorer selected zero final-test reviews under the primary cost; record this as a negative result. |
| C301 | M3 | Capacity frontier | Review policies | final_test | utility vs capacity | MUST | DONE | Conformal interval review is strongest non-oracle: +28.57 per app at 5%, +27.10 at 10%, +25.77 at 20% review and $10 cost. |
| C401 | M4 | Review-cost grid | Sensitivity | final_test | utility by cost | MUST | DONE | Positive at $5-$100 for 5%, 10%, and 20% capacities; negative at $100 for 30% and 50% capacities. |
| C402 | M4 | Wage/time/overhead grid | Cost anchors | final_test | review cost values | SHOULD | DONE | Anchor grid written to `review_cost_anchor_grid.csv`; source verification remains a writing/audit task. |
| C403 | M4 | Loss/profit ratio stress | Robustness | final_test | utility by ratio | SHOULD | DONE | At 10% review, conformal review is negative at ratios 1 and 2, weakly positive at 5, and clearly positive from 10 upward. |
| C501 | M5 | Write results summary | Reporting | outputs | markdown/CSV/JSON | MUST | DONE | Results written to `outputs/dean_cashflow_full/EXPERIMENT_RESULTS.md` and `refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md`. |
