# Reviewer Memory

## Round 1 - Teacher Review P0/P1 Supplement - Score: 4/10 top venue, 8/10 MSc

- **Suspicion**: The P0 claim audit is only keyword screening. It concatenates mixed sources, so safe wording in one file can hide unsafe wording elsewhere.
- **Unresolved**: `CLAIMS_FROM_RESULTS.md` is stale after the 2026-05-18 supplement and still lists manual-review residual-error sensitivity as future work.
- **Unresolved**: C4 must not be framed as selective cost dominance. At review multiplier 0.10, all-review is cheaper than split conformal under the same perfect-review assumptions.
- **Unresolved**: Manual-review residual-error sensitivity only compares selective review against automated threshold baselines unless all-review residual-error rows are added.
- **Pattern**: The new P1 analyses are useful, but they need stricter placement: temporal default-rate summary and FN:FP 5:1 cost thresholding can enter main text; PSI/KS, alpha grids, cohort profile, profit scenarios, and manual-review sensitivity mostly belong in appendix or limitations.
- **Accepted after debate**: Temporal wording is adequate if limited to upward default prevalence and modest feature movement, with no causal drift, strong covariate shift, or temporal degradation language.

## Round 2 - Teacher Review P0/P1 Supplement - Score: 4.5/10 top venue, 8.8/10 MSc

- **Previous suspicions addressed?**: Yes for MSc integration. The P0 table was relabeled as keyword screening, `CLAIMS_FROM_RESULTS.md` was updated, and a source-specific audit was added.
- **Resolved**: Title-level `Deployment-Ready` wording was replaced with `Deployment-Oriented` in D-CRED/README and NTU dissertation source.
- **Resolved**: C4 now includes the all-review caveat. Split conformal is framed as limited automation plus review burden, not cost dominance.
- **Resolved**: Manual-review residual-error sensitivity is scoped as a stylized stress test against automated threshold baselines.
- **Unresolved / disclosure only**: Validation reuse, no separate conformal holdout, RF/XGB 50k cap, public-data deployment limits, no fairness/reject-inference evidence, and synthetic profit/LGD/ROI scenarios.
- **Final MSc judgment**: Ready for integrating the teacher-review P0/P1 supplement into the dissertation with limitations preserved.

## Round 1 - Reject-Option Capacity Rerun - Score: 4/10 top venue, 8/10 MSc

- **New P0**: The 2026-05-19 reject-capacity rerun still violates its strongest locked-test story. It computes all-candidate `final_test` appendix metrics before primary-source freeze. The reviewer accepted that this is not test-Brier source-selection leakage, but it is not a pristine locked-final-test protocol.
- **Resolved old issue**: The 50k-cap objection is fixed for `outputs/reject_capacity_full`; `tree_max_train_rows` is null and LR/LGBM/XGB use full rows for the new main evidence.
- **Partially resolved old issue**: Validation reuse is mostly fixed at row level through `calibration_fit`, `calibration_select`, `policy_tune`, `risk_calibration`, and `final_test`; however, the split is row-wise chronological, not month-blocked.
- **Unresolved claim risk**: Unlimited reject option is not the empirical win. In the primary scenario it reviews 99.1% and is effectively all-review; the supported contribution is the capacity-aware cost frontier under stated assumptions.
- **Unresolved claim risk**: `lgbm/sigmoid` is selected by the pre-registered `calibration_select` rule only; do not claim it is robustly or scientifically best.
- **Unresolved claim risk**: Venn-Abers fallback and empirical conformal risk control must stay appendix/baseline diagnostics with no formal guarantee language.
