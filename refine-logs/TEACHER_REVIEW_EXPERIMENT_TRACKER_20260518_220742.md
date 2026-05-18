# Teacher Review P0/P1 Experiment Tracker

Updated: 20260518_220742

| Run ID | Milestone | Purpose | Priority | Status | Notes |
|---|---|---|---|---|---|
| R001 | M0 | Verify calibration-selection wording | P0 MUST | DONE | P0 audit written; validation selection remains explicit. |
| R002 | M0 | Lock required limitation block | P0 MUST | DONE | Limitations checked: validation reuse, 50k cap, LightGBM-RF, bootstrap subset, reduced seeds. |
| R003 | M0 | Remove deployment and automation overclaims | P0 MUST | DONE | Audit keeps C1/C4 conservative and flags production/fairness/reject-inference as limitations. |
| R101 | M1 | Compute PSI/KS drift table | P1 MUST | DONE | Wrote temporal_feature_shift_psi_ks.csv. |
| R102 | M1 | Produce temporal-shift summary figure/table | P1 MUST | DONE | Wrote temporal_drift_summary.csv and default-rate figure. |
| R201 | M2 | Aggregate selective alpha/review-cost trade-off | P1 MUST | DONE | Wrote selective_alpha_review_cost_tradeoff.csv from review_round1_fix. |
| R202 | M2 | Reconstruct reviewed-cohort profile if feasible | P1 SHOULD | DONE | Recomputed temporal masks and wrote cohort profile. |
| R203 | M2 | Add all-review or no-review reference if cheap | P1 SHOULD | DONE | Wrote selective_reference_policies.csv. |
| R301 | M3 | Manual-review residual-error sensitivity | P1 MUST | DONE | Wrote sensitivity table when row-level masks were recomputed. |
| R302 | M3 | Break-even residual-error calculation | P1 SHOULD | DONE | Wrote break-even table when row-level masks were recomputed. |
| R401 | M4 | Summarise cost-ratio policies | P1 MUST | DONE | Wrote cost_policy_scenario_summary.csv and delta summary. |
| R402 | M4 | Summarise LGD/ROI profit scenarios | P1 SHOULD | DONE | Wrote profit_policy_scenario_summary.csv as scenario-only evidence. |
| R501 | M5 | Produce paper-ready result tables | P1 MUST | DONE | Wrote TEACHER_REVIEW_EXPERIMENT_RESULTS.md and source map. |
| R502 | M5 | Update claim-boundary text | P0 MUST | PARTIAL | Generated claim-boundary text; dissertation source was not edited in this experiment run. |
| R503 | M5 | Final claim audit against CSVs | P0 MUST | DONE | Wrote p0 audit and number_source_map.csv. |
