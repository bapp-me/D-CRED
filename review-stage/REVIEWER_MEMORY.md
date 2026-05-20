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

## Round 1 - Reviewer-Response Nightmare Review - Score: 1.5-2/10 top venue, 6.5-7/10 MSc

- **Resolved**: The advisor month-blocked evidence is strong enough for the supervisor's stated MSc-level temporal-protocol critique. The month audit is clean, `lgbm/sigmoid` remains selected, and the capacity frontier is monotone.
- **Unresolved blocker**: The dean cash-flow run has a feature-separation contradiction. `funded_amnt` is included in the predictor groups while also being treated as a cash-flow/outcome column and marked disallowed in the audit. The experiment should be rerun without it, or reframed as post-funding analysis.
- **Unresolved claim risk**: Cash regression quality is weak; realized policy comparison is safer than any strong expected net-cash prediction claim.
- **Unresolved claim risk**: Predicted VOI is a negative result and must not be described as the winning method. Conformal interval review is the strongest non-oracle rule in the current run.
- **Unresolved writing risk**: Older proxy-only dean statements remain in advisor handoff files and can mislead future writing unless marked superseded.
- **Claim boundary**: The safe MSc story is accepted/funded-loan, observed-cash-flow decision analysis under month-blocked evaluation. It is not reject inference, not real human-review superiority, not FICO-specific, and not a top-tier ML contribution.

## Repair Follow-up - Dean Cash-Flow Clean Rerun

- **Addressed locally**: `funded_amnt` was removed from predictor groups and the dean cash-flow experiment was rerun under `outputs/dean_cashflow_full/`.
- **Addressed locally**: The feature audit now marks `funded_amnt` and other cash-flow/post-origination columns as disallowed predictors.
- **Still a claim boundary**: The rerun supports accepted-loan realized policy comparison, not full applicant-pool decisioning or reject inference.
- **Still unresolved for top-tier**: Predicted VOI remains a negative result and cash regression remains weak, so the safe story is decision analysis rather than a new high-performing learned VOI method.
