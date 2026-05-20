# Dean Cash-Flow Experiment Tracker

Updated: 2026-05-19 23:40

Primary run: `outputs/dean_cashflow_full`

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| C001 | M0 | Verify `loan.csv` schema | Data audit | full raw file | required fields | MUST | DONE | Cash-flow columns were present: `funded_amnt`, `total_rec_prncp`, `total_rec_int`, `total_rec_late_fee`, `recoveries`, `collection_recovery_fee`. |
| C002 | M0 | Build terminal accepted-loan sample | Data prep | terminal statuses | rows, status mix | MUST | DONE | Terminal sample has 1,306,387 rows; censored Current/Late/In Grace rows excluded. |
| C003 | M0 | Construct `net_cash` outcome | Cash-flow labels | terminal loans | profit/loss distribution | MUST | DONE | Cash-flow fields are outcomes only and are not predictors. |
| C004 | M0 | Build month-blocked roles | Split protocol | terminal loans | no shared month | MUST | DONE | Final test is 2017-11 through 2018-12, 67,461 rows; month audit has no shared month. |
| C101 | M1 | Train cheap PD/cash models | Cheap features | model_train | AUC, Brier, cash error | MUST | DONE | Final-test cheap PD AUC 0.6465; cash MAE 4076.8. |
| C102 | M1 | Train full PD/cash models | Full review features | model_train | AUC, Brier, cash error | MUST | DONE | Final-test full PD AUC 0.6772; cash MAE 3786.1. Some all-missing full numeric fields were skipped by sklearn. |
| C103 | M1 | Economic utility policies | Fixed/tuned/cash | final_test | realized utility | MUST | DONE | Tuned cash model is best among direct policies at -24.1 per application, versus tuned PD -109.1 and fixed PD -518.1. |
| C201 | M2 | Fit VOI scorer | `g(x_cheap)` | policy_tune | downstream utility | MUST | DONE | Predicted-VOI scorer selected zero final-test reviews under the primary cost; record this as a negative result. |
| C301 | M3 | Capacity frontier | Review policies | final_test | utility vs capacity | MUST | DONE | Conformal interval review produced the strongest non-oracle frontier: +26.95 per application at 5% review and $10 cost. |
| C401 | M4 | Review-cost grid | Sensitivity | final_test | utility by cost | MUST | DONE | Conformal review remains positive from $5 to $100 review cost, but ROI declines as cost and capacity rise. |
| C402 | M4 | Wage/time/overhead grid | Cost anchors | final_test | review cost values | SHOULD | DONE | Anchor grid written to `review_cost_anchor_grid.csv`; source verification remains a writing/audit task. |
| C403 | M4 | Loss/profit ratio stress | Robustness | final_test | utility by ratio | SHOULD | DONE | At 10% review, conformal review turns positive once loss/profit ratio reaches 10x; ratio 11.4 gives +12.18 per application. |
| C501 | M5 | Write results summary | Reporting | outputs | markdown/CSV/JSON | MUST | DONE | Results written to `outputs/dean_cashflow_full/EXPERIMENT_RESULTS.md` and `refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md`. |
