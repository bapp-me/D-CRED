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

## Round 2 - Blind-Review Response Bundle - Score: 1.8/10 top venue, 6.8/10 MSc

- **Resolved partially**: The blind-review bundle now contains real artifacts for cost sensitivity, capacity CI/baselines, cash-flow approval frontier, responsible-credit audit, and all-field audit.
- **New P0**: `locked_final_protocol` is not a true frozen rerun; tracker marks BR201/BR202 as `DONE_REUSED`, and the 2026-05-20 package points back to pre-existing 2026-05-19/2026-05-20 source runs.
- **Unresolved claim risk**: The cash-flow layer is still a negative result. `cashflow_coverage_constrained_best_policy.csv` selects `pd_risk_ranking` at every approval target, and all deployable mean net cash values remain negative.
- **Unresolved claim risk**: The capacity frontier is better framed now, but D-CRED does not cleanly separate from uncertainty at the CI level; empirical-risk baseline is partly degenerate above 20% capacity.
- **Unresolved claim risk**: The responsible-credit audit is too shallow for strong deployment-oriented wording. It lacks direct with/without-zip outputs and policy-conditioned utility/realized-cost columns; most `zip3` rows are small-cell suppressed.
- **Unresolved disclosure**: The strict/default/expanded feature stress test is only a 400k-row sanity cap and should not be sold as a full-data blind-review closure.
- **Process risk**: BR703/BR704 remain pending unless the handoff and thesis claim-control files are updated to the downgraded wording.

## Round 3 - Closure-Safe Blind-Review Response - Score: 2.3/10 top venue, 8.2/10 MSc

- **Resolved**: The locked-final objection is now genuinely fixed at MSc level. `blind_review_locked_rerun_20260520-231339` contains a pre-run manifest/config before selected predictions and final decisions, uses month-blocked roles, and writes selected-only final-test evidence.
- **Resolved**: Month-blocked protocol is clean: all 139 issue months are assigned to one role only.
- **Resolved**: The dean cash-flow `funded_amnt` predictor contradiction is fixed in `dean_cashflow_full`; cash-flow and post-origination fields are disallowed predictors.
- **Resolved for process**: BR703 handoff sync is done, and the closure-safe claim-control file is mirrored into `paper_writing_handoff_20260511`.
- **Partially resolved**: Capacity evidence is MSc-usable but not a top-tier algorithmic win. D-CRED improves over no-review/random at constrained capacity, but is identical to empirical-risk in the matched frontier and overlaps uncertainty-review CIs.
- **Partially resolved**: Responsible-credit audit now includes policy-conditioned costs and zip/no-zip capped stress, but remains only a risk-exposure audit, not fairness/legal compliance evidence.
- **Disclosure only**: Strict/default/expanded feature stress is deterministic 50k-row same-model capped evidence. Acceptable only if disclosed as resource-bounded.
- **Unresolved claim boundary**: Cash-flow remains negative/mixed. PD risk ranking is selected at every approval target and deployable mean net cash remains negative; cash regression R2 is negative.
- **Unresolved writing gate**: BR704 thesis claim audit remains pending after thesis integration.
- **Final MSc judgment**: The experiment/review loop can stop as expert-recognized for MSc claim-controlled writing, but the thesis is not final-submission-ready until BR704 confirms the revised text preserves these boundaries.
