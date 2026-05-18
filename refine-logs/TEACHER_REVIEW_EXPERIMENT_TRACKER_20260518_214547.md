# Teacher Review P0/P1 Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | Verify calibration-selection wording | Code + thesis draft audit | Lending temporal | validation-vs-test selection checklist | P0 MUST | TODO | Confirm selection is validation Brier; test Brier is reporting only |
| R002 | M0 | Lock required limitation block | Claim-control audit | All reported protocols | limitation coverage checklist | P0 MUST | TODO | Include validation reuse, 50k cap, LightGBM-RF surrogate, deterministic bootstrap subset, 3 reduced seeds |
| R003 | M0 | Remove deployment and automation overclaims | Thesis draft audit | All chapters | unsupported-claim checklist | P0 MUST | TODO | No SOTA, no production-bank, no high-automation, no fairness compliance |
| R101 | M1 | Compute PSI/KS drift table | Dataset-level temporal diagnostics | Lending train/val/test | PSI, KS, default rate | P1 MUST | TODO | Use allowed application-time features only |
| R102 | M1 | Produce temporal-shift summary figure/table | Dataset-level temporal diagnostics | Lending by quarter | default rate trend, partition summary | P1 MUST | TODO | Supports bounded C1; does not claim temporal AUC is worse |
| R201 | M2 | Aggregate selective alpha/review-cost trade-off | Existing selective results | Lending temporal | automation, review, cost, coverage | P1 MUST | TODO | Start from `outputs/review_round1_fix/selective_results.csv` |
| R202 | M2 | Reconstruct reviewed-cohort profile if feasible | Diagnostic mask recomputation | Lending temporal | cohort feature means, default rate | P1 SHOULD | TODO | If masks are hard to reconstruct, move to appendix/optional |
| R203 | M2 | Add all-review or no-review reference if cheap | Cost reference analysis | Lending temporal | expected cost, review rate | P1 SHOULD | TODO | Helps answer "why not review everything?" |
| R301 | M3 | Manual-review residual-error sensitivity | Selective stress test | Lending temporal | adjusted expected cost | P1 MUST | TODO | Test 1%, 3%, 5%, 10% residual manual-review error |
| R302 | M3 | Break-even residual-error calculation | Selective stress test | Lending temporal | break-even reviewer error | P1 SHOULD | TODO | State if C4 survives realistic reviewer error |
| R401 | M4 | Summarise cost-ratio policies | Existing decision results | Lending temporal | expected cost, approval/rejection | P1 MUST | TODO | Reuse `decision_results.csv` |
| R402 | M4 | Summarise LGD/ROI profit scenarios | Existing decision results | Lending temporal | realized/expected profit | P1 SHOULD | TODO | Scenario analysis only; no production ROI claim |
| R501 | M5 | Produce paper-ready result tables | Aggregated P1 outputs | Lending temporal | tables ready for Ch. 5/appendix | P1 MUST | TODO | One main table per claim; details in appendix |
| R502 | M5 | Update claim-boundary text | Writing integration | Thesis chapters | claim wording checklist | P0 MUST | TODO | Keep C1/C4 conservative |
| R503 | M5 | Final claim audit against CSVs | Paper audit | All tables/claims | number-source checklist | P0 MUST | TODO | Every numeric claim must map to a CSV or generated table |

