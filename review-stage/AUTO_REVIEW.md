# Auto Review Loop: D-CRED

**Started**: 2026-05-04T00:44:57+08:00
**Topic**: D-CRED: Deployment-Ready Credit Risk Evaluation and Decisioning
**Mode**: Codex reviewer, medium difficulty, autonomous loop
**Max rounds**: 4

## Context Sources

- `D-CRED/README.md`
- `D-CRED/refine-logs/EXPERIMENT_TRACKER.md`
- `D-CRED/refine-logs/EXPERIMENT_CODE_REVIEW.md`
- `D-CRED/outputs/full/experiment_results.json`
- `D-CRED/outputs/full/lending_random_vs_temporal.csv`
- `D-CRED/outputs/full/calibration_results.csv`
- `D-CRED/outputs/full/decision_results.csv`
- `D-CRED/outputs/full/selective_results.csv`
- `D-CRED/outputs/full/bootstrap_ci.csv`
- `D-CRED/outputs/full/feature_audit_lending_club.csv`
- `D-CRED/outputs/full/split_summary.csv`
- `D-CRED/outputs/full_reduced/reduced_experiment_results.json`
- `D-CRED/outputs/full_reduced/reduced_protocol_results.csv`
- `D-CRED/outputs/full_reduced/reduced_selective_results.csv`
- `refine-logs/FINAL_PROPOSAL.md`
- `refine-logs/EXPERIMENT_PLAN.md`
- `review-stage/AUTO_REVIEW.md`
- `C:/Users/fucak/.codex/memories/MEMORY.md`
- `C:/Users/fucak/.codex/memories/rollout_summaries/2026-05-02T14-53-36-z38N-cpcl_to_gcam_credit_risk_pivot.md`
- `C:/Users/fucak/.codex/memories/rollout_summaries/2026-05-02T17-07-48-KBoq-gcam_experiment_pipeline_full_uci_gpu_deploy.md`

## Initialization Notes

- Fresh loop for D-CRED. The root `review-stage/REVIEW_STATE.json` is a completed prior CPCL loop and is treated as historical context only.
- Reviewer agent: `019deeba-5a90-7ab2-a9ff-c80194adfcab`.
- Key scope limits already identified before review: RF/XGB fit on a stratified 50k training subset for local stability; bootstrap CIs use a deterministic 50k test-observation subset; reduced UCI/German protocol has three seeds and no temporal claim.

## Round 1 (2026-05-04T00:44:57+08:00)

### Assessment (Summary)

- Score: 4/10 for top ML venue; 8/10 for MSc dissertation readiness.
- Verdict: ALMOST for MSc dissertation results chapter; NOT READY for top venue.
- Key criticisms:
  - Selective review cost used a false-negative-cost basis even though the narrative specified a false-positive-cost basis.
  - C1 should say temporal evaluation changes the deployment environment, not that temporal AUC is necessarily worse.
  - RF/XGB comparisons are limited by a 50k fit cap and an RF-style LightGBM surrogate.
  - Validation data are reused for calibration, threshold selection, and conformal quantiles.
  - Decision uncertainty needs delta uncertainty for the actual decision claims.

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

1. **Score**
- Top ML venue: **4/10**
- MSc dissertation readiness: **8/10**

2. **Verdict**
- MSc dissertation results chapter: **ALMOST**
- Top venue: **NOT READY**

3. **Critical weaknesses ranked by severity**
- **C4 is not yet cleanly defensible as written.** The stated review-cost assumption is `0.05/0.10/0.20 * false_positive_cost` in [EXPERIMENT_PLAN.md](/D:/code/diss_codex/refine-logs/EXPERIMENT_PLAN.md:154) and [FINAL_PROPOSAL.md](/D:/code/diss_codex/refine-logs/FINAL_PROPOSAL.md:181), but the implementation multiplies by `false_negative_cost` in [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:62) and [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:97). On Lending Club, split conformal then reviews about **91%** of cases and automates only **8-9%** with almost no auto-rejects in [selective_results.csv](/D:/code/diss_codex/D-CRED/outputs/full/selective_results.csv:11). This makes the selective pillar a narrow risk-control result, not a practical high-automation decision system.
- **C1 is overphrased relative to the evidence.** The temporal split clearly changes the population: default rate rises from about **0.1998** to **0.2179** in [split_summary.csv](/D:/code/diss_codex/D-CRED/outputs/full/split_summary.csv:2). But raw temporal ROC-AUC/PR-AUC are slightly **higher**, not lower, than random-split values in [lending_random_vs_temporal.csv](/D:/code/diss_codex/D-CRED/outputs/full/lending_random_vs_temporal.csv:2). The evidence supports “different and more deployment-relevant,” not a strong “random splits overstate performance” story.
- **Model-ranking claims are partly confounded by engineering substitutions.** `rf` is actually LightGBM RF, not sklearn RF, and both `rf` and `xgb` are trained on a **50k cap** while LR sees the full training split in [README.md](/D:/code/diss_codex/D-CRED/README.md:47), [EXPERIMENT_TRACKER.md](/D:/code/diss_codex/D-CRED/refine-logs/EXPERIMENT_TRACKER.md:70), and [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:417). That is acceptable for local execution, but it weakens any “model X beats model Y” interpretation.
- **The validation split is doing too many jobs.** The same validation data are used to fit calibrators, choose the best calibrator by Brier, choose thresholds, and compute conformal quantiles in [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:385), [decision.py](/D:/code/diss_codex/D-CRED/dcred/decision.py:154), and [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:75). That is not test leakage, but it is a softer protocol than the narrative suggests, especially for German/UCI.
- **Uncertainty reporting is still incomplete for the actual claims.** The plan asks for paired delta uncertainty in [EXPERIMENT_PLAN.md](/D:/code/diss_codex/refine-logs/EXPERIMENT_PLAN.md:205), but the repo stores pointwise CIs only for ROC-AUC, Brier, and fixed-0.5 cost on a deterministic **50k** test subset in [bootstrap_ci.csv](/D:/code/diss_codex/D-CRED/outputs/full/bootstrap_ci.csv:2) and [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:453). There are no paired CIs for the improvements that support C3 or C4.

4. **Minimum fixes ranked**
- **Rewrite the claims to the narrower story the data support.** C1 should be “temporal evaluation changes the operating environment,” not “temporal is worse.” C4 should be “very conservative auto-approval with heavy review,” not “practical selective automation.”
- **Fix or relabel the selective review-cost convention.** Either recompute with the intended `false_positive_cost` basis, or state explicitly that the reported review cost is a fraction of `false_negative_cost`.
- **Add one clear limitations block.** Include: 50k tree cap, LightGBM-RF surrogate, single validation split reused for calibration/threshold/conformal, deterministic 50k bootstrap subset, and only 3 reduced-protocol seeds.
- **Report paired deltas for the key decisions.** Minimum viable set: `fixed_0.5 -> cost_5_to_1`, and `cost_5_to_1 -> split_conformal`, with paired bootstrap or at least seed-level delta summaries.
- **Aggregate the reduced results in-repo.** Right now UCI/German support exists, but the chapter should not rely on ad hoc inspection of per-seed rows.

5. **Claims C1-C5**
- **C1: Partially supported.** Temporal vs random differs materially in base rate and calibration, but not in the simple “temporal hurts AUC” sense.
- **C2: Supported.** Calibration changes probability quality, and ranking is not invariant across ROC-AUC, Brier, and expected-cost views.
- **C3: Supported.** Fixed `0.5` is clearly inferior to cost-aware thresholds; e.g. LR temporal cost drops from **1.0656** to **0.6645** in [decision_results.csv](/D:/code/diss_codex/D-CRED/outputs/full/decision_results.csv:3) and [decision_results.csv](/D:/code/diss_codex/D-CRED/outputs/full/decision_results.csv:63).
- **C4: Partially supported.** The selective layer reduces automatic approved-default risk and expected cost under the implemented convention, but automation is very low on Lending Club and the review-cost basis is mismatched.
- **C5: Partially supported.** The scope separation is honest, and UCI/German do reproduce cost-sensitive findings, but the reduced evidence is noisy, under-aggregated, and not strong external validation.

6. **Unsupported claims, cherry-picking risks, metric mistakes, leakage risks, missing baselines, protocol concerns**
- **Unsupported if stated strongly:** “out-of-time performance is worse than random split,” and “selective review works at practical automation on Lending Club.”
- **Cherry-picking risk:** only showing best temporal calibrated rows can hide that reduced-protocol calibration winners are unstable across seeds, and that the selective system is mostly “review almost everything.”
- **Metric mistake:** the review-cost multiplier is attached to the wrong base cost in the implementation.
- **Leakage risk:** direct label/timestamp leakage looks low; the bigger issue is protocol reuse of the same validation split, not obvious target leakage.
- **Missing baselines/analyses:** no contaminated-feature stress test, no rolling temporal split, no paired CI on the actual decision improvements, no separate conformal-calibration holdout.
- **Audit limitation:** the “feature audit” is mostly a curated 10-feature granting-data protocol in [feature_audit_lending_club.csv](/D:/code/diss_codex/D-CRED/outputs/full/feature_audit_lending_club.csv:2), not a raw-feature contamination audit.

7. **Should the auto-review loop stop?**
- **Continue another round after fixes.**
- This does **not** need a big new experiment by default. One round focused on claim control, selective-cost correction/relabeling, reduced-result aggregation, and explicit limitations is the right move.
- The defensible chapter is the narrower one: calibration and cost-aware thresholding are solid; selective decisioning is currently a conservative review-heavy control layer, not a deployment-ready automation win.

</details>

### Actions Taken

- Fixed selective decisioning so review-cost multipliers use the planned false-positive-cost basis rather than the false-negative-cost basis.
- Added `cost_values` and paired bootstrap delta reporting for decision costs.
- Added `outputs/review_round1_fix/decision_delta_ci.csv` from a fresh Lending-only rerun.
- Added `scripts/summarize_review_fixes.py` and generated stable review-stage summaries:
  - `review-stage/lending_decision_delta_summary.csv`
  - `review-stage/lending_decision_delta_ci.csv`
  - `review-stage/reduced_calibration_summary.csv`
  - `review-stage/reduced_cost_summary.csv`
  - `review-stage/reduced_selective_summary.csv`
  - `review-stage/ROUND1_FIX_SUMMARY.md`
- Updated `D-CRED/README.md`, `D-CRED/refine-logs/EXPERIMENT_TRACKER.md`, `refine-logs/FINAL_PROPOSAL.md`, and `refine-logs/EXPERIMENT_PLAN.md` to narrow C1/C4 and state limitations.
- Updated `run_all` so reduced-protocol outputs go to a sibling `_reduced` directory and run with CPU XGBoost for local stability.

### Results

- Verification: `python -m compileall dcred scripts` passed.
- Fresh Lending fix run completed: `python -m dcred.cli run-lending --run-name review_round1_fix --models lr rf xgb --rf-estimators 100 --xgb-estimators 300 --use-gpu-xgb --bootstrap 200 --tree-max-train-rows 50000 --n-jobs 1`.
- Corrected split-conformal expected cost at alpha=0.10 and review multiplier=0.10:
  - LR: 0.1209 expected cost, 0.0934 automation, 0.9066 review.
  - RF-style LightGBM: 0.1161 expected cost, 0.0779 automation, 0.9221 review.
  - XGB: 0.1182 expected cost, 0.0904 automation, 0.9096 review.
- Paired bootstrap expected-cost deltas on deterministic 50k test subset:
  - `cost_5_to_1_minus_fixed_0.5`: negative for all three models.
  - `split_conformal_alpha_0.10_review_0.10_minus_robust_cost`: negative for all three models under the corrected review-cost convention.
  - Interpretation remains conservative because automation is only about 8-9%.

### Status

Continuing to Round 2 re-review after targeted fixes.

## Round 2 (2026-05-04T01:02:00+08:00)

### Assessment (Summary)

- Score: 4/10 for top ML venue; 8.5/10 for MSc dissertation readiness.
- Verdict: READY for MSc dissertation results chapter; NOT READY for top venue.
- Key criticisms:
  - Major Round 1 validity bug is resolved.
  - Decision-delta uncertainty and reduced-result aggregation are now present.
  - Remaining issues are reporting limits: manual review is modeled as cost-only, Lending Club conformal is mostly approve-or-review, and validation reuse / 50k caps remain limitations.

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

1. **Updated score**
- Top ML venue: **4/10**
- MSc dissertation readiness: **8.5/10**

2. **Updated verdict**
- MSc dissertation results chapter: **READY**
- Top venue: **NOT READY**

3. **Round 1 concerns**
- **Resolved**
  - **Selective review-cost bug:** fixed in [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:56), [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:84), and [selective.py](/D:/code/diss_codex/D-CRED/dcred/selective.py:116). The fresh rerun in [selective_results.csv](/D:/code/diss_codex/D-CRED/outputs/review_round1_fix/selective_results.csv:13) now matches the stated `false_positive_cost` basis.
  - **Paired decision-delta uncertainty:** added in [metrics.py](/D:/code/diss_codex/D-CRED/dcred/metrics.py:133) and wired in [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:521). The resulting [decision_delta_ci.csv](/D:/code/diss_codex/D-CRED/outputs/review_round1_fix/decision_delta_ci.csv:2) supports the main C3/C4 cost comparisons.
  - **Claim overstatement on C1/C4:** narrowed in [FINAL_PROPOSAL.md](/D:/code/diss_codex/refine-logs/FINAL_PROPOSAL.md:214) and [EXPERIMENT_PLAN.md](/D:/code/diss_codex/refine-logs/EXPERIMENT_PLAN.md:11), and summarized cleanly in [ROUND1_FIX_SUMMARY.md](/D:/code/diss_codex/D-CRED/review-stage/ROUND1_FIX_SUMMARY.md:5).
  - **Reduced-protocol aggregation:** addressed by [summarize_review_fixes.py](/D:/code/diss_codex/D-CRED/scripts/summarize_review_fixes.py:99) and the generated review-stage summaries such as [reduced_calibration_summary.csv](/D:/code/diss_codex/D-CRED/review-stage/reduced_calibration_summary.csv:1).

- **Partially resolved**
  - **Model-ranking confounds from engineering substitutions:** still present, but now disclosed in [README.md](/D:/code/diss_codex/D-CRED/README.md:48) and [EXPERIMENT_TRACKER.md](/D:/code/diss_codex/D-CRED/refine-logs/EXPERIMENT_TRACKER.md:83). The evidence is usable for an MSc chapter, but still weak for stronger model-comparison claims.
  - **Protocol limitations visibility:** improved in [README.md](/D:/code/diss_codex/D-CRED/README.md:66), [EXPERIMENT_TRACKER.md](/D:/code/diss_codex/D-CRED/refine-logs/EXPERIMENT_TRACKER.md:79), and [ROUND1_FIX_SUMMARY.md](/D:/code/diss_codex/D-CRED/review-stage/ROUND1_FIX_SUMMARY.md:10). I would still carry the same language directly into the dissertation chapter text, not leave it only in repo docs.

- **Unresolved**
  - **Validation reuse:** still the same validation split for calibration, threshold selection, and conformal quantiles; see [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:153), [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:173), and [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:554). This is acceptable if explicitly framed as a limitation, but it is not a stronger protocol now.
  - **Top-venue scope weakness:** unchanged. No new benchmark breadth, no separate conformal holdout, and the selective layer is still extremely review-heavy.

4. **Remaining minimum fixes**
- Put one explicit sentence in the results chapter that **reviewed cases are modeled as incurring review cost but no residual classification error**. That assumption is still optimistic and materially affects the selective-cost story.
- State that on Lending Club, split conformal behaved **mostly as approve-or-review, not approve/reject/review in balanced volume**: review is about **91%** and automatic reject is near zero in [selective_results.csv](/D:/code/diss_codex/D-CRED/outputs/review_round1_fix/selective_results.csv:13).
- Carry the limitations block directly into the dissertation writeup: 50k tree cap, LightGBM-RF surrogate, validation reuse, deterministic 50k bootstrap subset, and 3-seed reduced-protocol sanity checks.

These are reporting fixes, not new experiment blockers.

5. **Stop or continue**
- **Stop now for the MSc dissertation results chapter.**
- The important distinction is that the work is now **ready with limitations**, not “fully hardened.” The major Round 1 validity bug is fixed, the key delta claims now have supporting uncertainty, and the narrative is narrow enough to be defensible.
- **Continue to Round 3 only if the target shifts beyond MSc readiness** and you want to harden C4 further with a separate conformal holdout or a non-perfect-manual-review sensitivity model.

</details>

### Actions Taken

- Added the reviewer-requested reporting caveats to `D-CRED/dcred/decision.py`, `D-CRED/README.md`, `D-CRED/refine-logs/EXPERIMENT_TRACKER.md`, `refine-logs/EXPERIMENT_PLAN.md`, `refine-logs/FINAL_PROPOSAL.md`, and `D-CRED/review-stage/ROUND1_FIX_SUMMARY.md`.
- Specifically documented that reviewed cases incur review cost only and no residual manual-review error is estimated.
- Specifically documented that Lending Club split conformal behaves mostly as approve-or-review at the reported operating point.

### Results

- Verification: `python -m compileall dcred scripts` passed after the reporting and code-comment updates.
- Smoke verification: `python -m dcred.cli run-all --run-name run_all_smoke --models lr --bootstrap 0 --lending-max-rows 1000 --reduced-seeds 42 --n-jobs 1` passed and wrote separate `outputs/run_all_smoke/` and `outputs/run_all_smoke_reduced/` directories.

### Status

Stopping the loop for the MSc dissertation target: reviewer verdict is READY with limitations.

## Method Description

D-CRED is a deployment-oriented credit-risk evaluation and decisioning pipeline. It audits the Lending Club granting dataset into a curated application-time feature protocol, compares random and temporal 60/20/20 splits, trains scalable tabular baselines, applies raw/sigmoid/isotonic calibration, and evaluates lending decisions under fixed, F1, cost-sensitive, profit-sensitive, and robust thresholds.

The final decision layer includes conservative selective decisioning through uncertainty bands and split conformal prediction. In the current evidence, calibration and cost-aware thresholding are the strongest claims. Split conformal is best framed as a review-heavy risk-control layer: reviewed cases are modeled as paying review cost only, and the Lending Club operating point automates only about 8-9% of cases.

## Result-to-Claim Summary

- claim_supported: partial
- confidence: medium-high for MSc dissertation claims; low for top-venue claims
- supported: temporal evaluation changes the deployment operating environment; calibration improves probability quality; cost-aware thresholds improve expected cost versus fixed 0.5; selective decisioning can reduce expected cost under the stated cheap-review assumption.
- not supported: a general top-venue method contribution; uniformly worse temporal AUC; high-automation selective decisioning; production-bank deployment validity; strong model-family ranking claims.
- revised claim: D-CRED is supported as a deployment-ready evaluation and decision framework for an MSc dissertation, with the strongest evidence for calibration and cost-aware decisioning and a narrower conservative selective-review story.
- output: `D-CRED/CLAIMS_FROM_RESULTS.md`

## Final Summary

The loop stopped after Round 2 because the external reviewer judged the MSc dissertation results chapter READY with limitations. Remaining top-venue blockers are documented as limitations rather than immediate loop fixes: validation reuse, 50k tree fit cap, LightGBM-RF surrogate, deterministic 50k bootstrap subset, only three reduced-protocol seeds, and no separate conformal holdout.

---

# Hard Auto Review Loop: Teacher Review P0/P1 Supplement

**Started**: 2026-05-18T22:36:55+08:00
**Topic**: D-CRED teacher-review P0/P1 experiment supplement
**Mode**: Codex reviewer, hard difficulty, human checkpoint enabled
**Reviewer agent**: `019e3b7e-a214-7e20-a5f8-558ca25a59dd`

## Context Sources

- `refine-logs/TEACHER_REVIEW_EXPERIMENT_PLAN.md`
- `refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md`
- `refine-logs/TEACHER_REVIEW_EXPERIMENT_TRACKER.md`
- `outputs/teacher_review_p1_latest/`
- `scripts/teacher_review_p1_analysis.py`
- `CLAIMS_FROM_RESULTS.md`
- `review-stage/AUTO_REVIEW.md`
- `refine-logs/EXPERIMENT_CODE_REVIEW.md`
- `outputs/review_round1_fix/decision_results.csv`
- `outputs/review_round1_fix/selective_results.csv`
- `outputs/review_round1_fix/decision_delta_ci.csv`

## Round 1 (2026-05-18T22:36:55+08:00)

### Assessment (Summary)

- Score: 4/10 top venue; 8/10 MSc dissertation.
- Verdict: almost ready for integrating the teacher-review P0/P1 supplement.
- Key criticisms:
  - P0 claim-control audit is keyword screening, not a defensible source-specific audit.
  - `CLAIMS_FROM_RESULTS.md` is stale after the 2026-05-18 supplement.
  - Split conformal is cost-dominated by all-review at review multiplier 0.10 under perfect-review assumptions.
  - Manual-review residual-error sensitivity is a valid stylized stress test, but only against automated threshold baselines unless all-review residual-error rows are added.
  - Temporal evidence supports upward default prevalence and modest feature movement, not causal drift or strong covariate shift.

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

**Score And Verdict**
Top-venue score: **4/10**. MSc-dissertation score: **8/10**.

Verdict: **almost ready** for integrating the teacher-review P0/P1 supplement. The P1 analyses are real and mostly useful; the P0 claim-control gate is too shallow to trust as a pass, and the selective-decisioning cost story needs one stronger caveat before writing.

**Ranked Findings**
P0: The P0 audit is not a defensible claim audit. It concatenates mixed sources and passes broad keyword checks, so a stale or unsafe paragraph could be masked by safe wording elsewhere: [teacher_review_p1_analysis.py](/D:/code/diss_codex/D-CRED/scripts/teacher_review_p1_analysis.py:519), [teacher_review_p1_analysis.py](/D:/code/diss_codex/D-CRED/scripts/teacher_review_p1_analysis.py:523), [teacher_review_p1_analysis.py](/D:/code/diss_codex/D-CRED/scripts/teacher_review_p1_analysis.py:548). The audit says PASS: [p0_protocol_claim_audit.md](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/p0_protocol_claim_audit.md:14), but the tracker admits dissertation source was not edited in this run: [TEACHER_REVIEW_EXPERIMENT_TRACKER.md](/D:/code/diss_codex/D-CRED/refine-logs/TEACHER_REVIEW_EXPERIMENT_TRACKER.md:20). `CLAIMS_FROM_RESULTS.md` is also stale: it is dated 2026-05-04 and still lists manual-review residual-error sensitivity as a future experiment: [CLAIMS_FROM_RESULTS.md](/D:/code/diss_codex/D-CRED/CLAIMS_FROM_RESULTS.md:3), [CLAIMS_FROM_RESULTS.md](/D:/code/diss_codex/D-CRED/CLAIMS_FROM_RESULTS.md:56).

P1: The selective-cost interpretation omits the awkward all-review comparison. At review multiplier 0.10, all-review has expected cost 0.10 for all models, below split conformal's 0.116 to 0.121: [selective_reference_policies.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/selective_reference_policies.csv:3), [selective_reference_policies.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/selective_reference_policies.csv:10), [selective_alpha_review_cost_tradeoff.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/selective_alpha_review_cost_tradeoff.csv:6). So C4 should not be framed as "lower cost than review"; it buys about 8 to 9 percent automation while reviewing roughly 91 percent.

P1: Temporal drift is correctly mostly a base-rate story, but the word "drift" must stay bounded. Default rate rises from 0.1838 train to 0.2296 validation and 0.2179 test, while top PSI values are modest, 0.039 validation and 0.061 test: [temporal_drift_summary.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/temporal_drift_summary.csv:2), [temporal_drift_summary.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/temporal_drift_summary.csv:3). This supports "changed operating period / base-rate shift," not strong covariate drift or causal temporal degradation.

P1: Manual-review residual-error sensitivity is a reasonable stylized stress test, but its interpretation is incomplete. The formula adds `error_rate * mean(review_mask * class_cost)`, which is defensible as a simple residual classification-error penalty: [teacher_review_p1_analysis.py](/D:/code/diss_codex/D-CRED/scripts/teacher_review_p1_analysis.py:745), [teacher_review_p1_analysis.py](/D:/code/diss_codex/D-CRED/scripts/teacher_review_p1_analysis.py:759). But the break-even table compares only against robust/cost-threshold automated baselines, not all-review: [manual_review_break_even_error.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/manual_review_break_even_error.csv:4), [manual_review_break_even_error.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/manual_review_break_even_error.csv:13).

P2: Cost scenario consolidation supports C3 only under matched assumptions. `cost_5_to_1` beats fixed 0.5 under FN:FP 5 and 10, but is worse than fixed 0.5 under FN:FP 2: [cost_policy_delta_summary.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/cost_policy_delta_summary.csv:11), [cost_policy_delta_summary.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/cost_policy_delta_summary.csv:14), [cost_policy_delta_summary.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/cost_policy_delta_summary.csv:47). This is fine if written as "cost-aware thresholding under stated cost ratios," not "one threshold robustly improves ROI."

**Minimum Fixes**
Must-fix before writing: update `CLAIMS_FROM_RESULTS.md`; replace "deployment-ready" with "deployment-oriented"; remove residual-error sensitivity from future work; add the all-review caveat to C4; replace the P0 PASS table with a source-specific manual audit or mark it as keyword screening only.

Should-fix if time: add one row or paragraph comparing split conformal to all-review at review multipliers 0.10 and 0.50; add an all-review residual-error sensitivity reference; explicitly state that alpha changes coverage but barely changes action volumes.

Writing placement: main text gets temporal default-rate summary, cost-aware thresholding under FN:FP 5:1, and the selective operating point with the all-review caveat. Appendix gets PSI/KS, alpha/review-cost grid, cohort profile, and profit scenarios. Limitation/stress-test only gets manual-review residual-error sensitivity and validation reuse.

**Review Questions**
The P1 analysis genuinely answers much of the teacher review; it is not only cosmetic. The exception is P0, where the audit is mostly cosmetic.

Temporal drift is not badly overinterpreted in the generated summary, but any dissertation wording stronger than "mainly base-rate shift with modest feature-distribution movement" would overclaim.

Manual-review sensitivity is calculated reasonably for a stylized stress test. Its baseline interpretation is too narrow because all-review is not stress-tested alongside it.

Selective decisioning is mostly conservatively framed, but the cost framing needs to admit that cheap all-review can dominate selective cost under the same perfect-review assumption.

Cost/profit consolidation supports C3 as a stated-assumption expected-cost claim. It does not support production ROI. Profit tables should remain appendix-only.

I found no obvious test-label leakage. Remaining risks are validation reuse, best-calibration reuse, shallow P0 audit checks, and possible cherry-picking if the all-review baseline is hidden.

**Memory Update**
- Do not trust the P0 PASS table unless it is replaced by source-specific claim auditing.
- C4 must be written as review-burden/risk-control evidence, not selective cost dominance.
- The all-review baseline is the key unresolved comparator for selective decisioning at cheap review cost.
- Temporal evidence is base-rate shift plus modest PSI/KS, not strong covariate drift.
- `CLAIMS_FROM_RESULTS.md` is stale after the 2026-05-18 supplement and should be updated before the next round.

</details>

### Debate Transcript (hard mode)

#### Executor Rebuttal Summary

- Accepted that the P0 audit is only keyword screening and proposed downgrading it plus updating `CLAIMS_FROM_RESULTS.md`.
- Partially accepted the all-review criticism: all-review is cheaper at review multiplier 0.10 under perfect-review assumptions, while split conformal offers limited automation.
- Partially accepted the manual-review sensitivity criticism: the formula is a valid stylized stress test against automated baselines but does not test all-review.
- Accepted bounded temporal wording: upward default prevalence plus modest feature movement only.

#### Reviewer Ruling

1. **P0 audit weakness: accepted, unresolved until implemented.** Minimum required: label the P0 audit as keyword screening only, update `CLAIMS_FROM_RESULTS.md`, and perform a source-specific final dissertation claim audit.
2. **All-review baseline weakness: partially accepted.** Minimum required: state that split conformal is cost-dominated by all-review at review multiplier 0.10 under perfect-review assumptions, but offers limited automation; put the all-review comparison in main text or adjacent appendix.
3. **Manual-review residual-error baseline weakness: accepted, unresolved unless scoped.** Minimum required: either add all-review residual-error rows or explicitly state the sensitivity only compares selective review against automated threshold baselines and cannot establish selective cost dominance.
4. **Temporal drift wording: accepted with bounded wording.** Main text should say default prevalence shifted upward and feature movement was modest; no causal drift, strong covariate shift, or temporal degradation language.

### Actions Taken

- Hard-review raw response and debate ruling recorded.
- `review-stage/REVIEWER_MEMORY.md` initialized for this hard-mode supplement review.
- No experiment/code/document fixes have been implemented yet because human checkpoint is enabled.

### Status

Waiting at human checkpoint before Phase C.

## Round 2 (2026-05-18T23:10:00+08:00)

### Assessment (Summary)

- Score: 4.5/10 top venue; 8.8/10 MSc dissertation.
- Verdict: ready for integrating the teacher-review P0/P1 supplement into the dissertation, with limitations preserved.
- Key outcomes:
  - `CLAIMS_FROM_RESULTS.md` is no longer stale and now uses deployment-oriented framing.
  - P0 audit outputs are labeled `SCREEN`, not `PASS`, and are explicitly keyword screening only.
  - All-review residual-error reference is present; split conformal is no longer framed as cost dominance.
  - Manual-review residual-error sensitivity is scoped as a stylized stress test against automated threshold baselines.
  - Dissertation source now carries the all-review caveat and no longer has `Deployment-Ready` matches in the checked files.

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

**Score:** top-venue **4.5/10** / MSc-dissertation **8.8/10**

**Verdict:** **ready** for integrating the teacher-review P0/P1 supplement into the dissertation, with the existing limitations preserved.

The Round 1 blockers are resolved enough for MSc integration. `CLAIMS_FROM_RESULTS.md` is no longer stale: it is dated 2026-05-18, uses "deployment-oriented," states the all-review caveat, scopes manual-review sensitivity, and labels the P0 tables as keyword screening only ([CLAIMS_FROM_RESULTS.md](/D:/code/diss_codex/D-CRED/CLAIMS_FROM_RESULTS.md:3), [CLAIMS_FROM_RESULTS.md](/D:/code/diss_codex/D-CRED/CLAIMS_FROM_RESULTS.md:27), [CLAIMS_FROM_RESULTS.md](/D:/code/diss_codex/D-CRED/CLAIMS_FROM_RESULTS.md:57)). The generated audit now says `SCREEN`, not `PASS`, and warns that it is not source-specific proof ([p0_protocol_claim_audit.md](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/p0_protocol_claim_audit.md:1), [p0_protocol_claim_audit.md](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/p0_protocol_claim_audit.md:8)).

The all-review caveat is now sufficient. The key numbers are present: split conformal at multiplier 0.10 costs 0.116-0.121 with 7.8-9.3% automation, while all-review costs 0.100 at zero residual error and remains lower across the tested 1/3/5/10% residual-error rows under the same stylized class-error model ([selective_operating_point.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/selective_operating_point.csv:2), [all_review_residual_error_reference.csv](/D:/code/diss_codex/D-CRED/outputs/teacher_review_p1_latest/all_review_residual_error_reference.csv:7)). I do not require another figure; an appendix table plus the current main-text caveat is enough.

Manual-review residual-error sensitivity is now safely scoped. The result summary explicitly says selective rows compare against automated threshold baselines only, not all-review dominance ([TEACHER_REVIEW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md:42), [TEACHER_REVIEW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md:96)). Dissertation text also reflects this in Chapter 6 ([chapter-6.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-6/chapter-6.tex:54)).

The problematic overclaim has been removed. I found no remaining `Deployment-Ready` matches in the requested files. The dissertation now says "deployment-oriented" and explicitly rejects high-automation or all-review cost-dominance claims in the abstract, Chapter 1, Chapter 5, Chapter 6, and Chapter 7 ([abstract.tex](/D:/code/diss_codex/ntu-dissertation/latex/c-front-matter/abstract.tex:13), [chapter-5.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-5/chapter-5.tex:134), [chapter-7.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-7/chapter-7.tex:14)). `python -m compileall dcred scripts` also passed.

**Remaining Risks**
No remaining P0/P1 blockers for MSc integration. Residual risks are disclosure items: validation reuse remains a softer protocol, RF/XGB training caps still weaken model-ranking claims, and profit/LGD/ROI rows remain scenario evidence only ([chapter-6.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-6/chapter-6.tex:42), [chapter-6.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-6/chapter-6.tex:40), [chapter-6.tex](/D:/code/diss_codex/ntu-dissertation/latex/chapter-6/chapter-6.tex:52)).

**Placement Guidance**
Main text: bounded temporal default-rate shift, FN:FP 5:1 cost-aware thresholding, split-conformal operating point with all-review caveat.

Appendix: PSI/KS feature-shift table, alpha/review-cost grid, reviewed-cohort profile, all-review residual-error reference, profit/LGD/ROI scenario tables.

Limitations: validation reuse, manual-review residual-error not measured, no production-bank validation, no fairness/reject-inference solution, RF/XGB 50k cap.

**Memory Update**
- Round 1 P0 audit objection is resolved by relabeling keyword screening and adding a source-specific audit.
- C4 is now acceptable only as limited automation plus review-burden analysis; all-review remains a required comparator.
- Manual-review sensitivity is safe only as a stylized stress test against automated threshold baselines unless all-review is shown alongside it.
- Top-venue blockers remain unchanged: validation reuse, no separate conformal holdout, public-data deployment limits, no production/fairness/reject-inference evidence.

</details>

### Actions Taken

- Updated `CLAIMS_FROM_RESULTS.md` to 2026-05-18 claim boundaries, including all-review caveat and manual-review sensitivity scope.
- Updated `scripts/teacher_review_p1_analysis.py` so future P0 audit outputs are keyword screening with `SCREEN` status, not `PASS`.
- Updated current `outputs/teacher_review_p1_latest/` and timestamped P1 run artifacts with `SCREEN` audit status and all-review residual-error reference.
- Added `refine-logs/TEACHER_REVIEW_SOURCE_SPECIFIC_CLAIM_AUDIT.md`.
- Replaced title-level `Deployment-Ready` wording with `Deployment-Oriented` in D-CRED README and NTU dissertation source.
- Added all-review caveats to `abstract.tex`, `chapter-1.tex`, `chapter-5.tex`, `chapter-6.tex`, and `chapter-7.tex`.

### Results

- Verification: `python -m compileall dcred scripts` passed.
- Verification: `rg -n -i "Deployment-Ready" D:\code\diss_codex\D-CRED\README.md D:\code\diss_codex\ntu-dissertation\latex D:\code\diss_codex\D-CRED\CLAIMS_FROM_RESULTS.md` returned no matches.
- Reviewer verdict: ready for MSc integration with limitations preserved.

### Status

Completed for the MSc teacher-review P0/P1 supplement target.

## Final Summary - Teacher Review P0/P1 Supplement

The hard auto-review loop stopped after Round 2 because the reviewer judged the supplement ready for MSc dissertation integration. The important claim-control changes are now explicit: P0 tables are screening aids only, temporal evidence is mainly base-rate shift plus modest feature movement, C3 is strongest under matched cost ratios, and C4 is limited automation with review burden rather than all-review cost dominance.

## Round 1 - Reject-Option Capacity Rerun Hard Review (2026-05-19)

### Assessment (Summary)

- MSc defense readiness: 8/10.
- Top-venue readiness: 4/10.
- MSc verdict: almost ready.
- Top-venue verdict: not ready.
- Main protocol ruling after debate: the new run fixes the old 50k cap and explicit test-Brier source selection, and mostly fixes validation reuse at row level. It does not support the strongest "final_test read once after freeze" wording because the current code computes all-candidate final-test appendix metrics before selecting the primary source.
- Main claim ruling: the useful revised thesis is the capacity-aware cost frontier under stated review-cost and residual-error assumptions. Unlimited reject option is not a strong empirical win because it degenerates to near all-review under cheap review.

### Key Criticisms

- The locked final-test claim is too strong for the current implementation. The reviewer accepted that this is not test-Brier selection leakage, but kept it as a live protocol blemish.
- The seven-role split is row-wise chronological and row-disjoint, but not month-blocked; adjacent roles share boundary months.
- The `lgbm/sigmoid` source is selected by the pre-registered `calibration_select` rule, not proven generally superior.
- Venn-Abers is only an empirical binomial interval fallback, and empirical conformal risk control is a held-out risk-threshold diagnostic, not a formal guarantee.
- Root-level claim-control files still need synchronization with the new run; old 50k/validation-reuse limitations remain in historical docs and must not be mistaken for current-run evidence.

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

1. **Scores**

MSc defense readiness: **8/10**  
Top-venue readiness: **4/10**

2. **Verdict**

MSc defense: **almost ready**  
Top venue: **not ready**

3. **Findings ordered by severity**

- **[P0] The claimed locked `final_test` protocol is false in the implementation.**  
  Evidence: the protocol says `final_test` should not be used for selection and may be read once after the source/scenario are fixed in `selection_protocol.md`. But the code writes per-calibrator `final_test` metrics before selecting the primary source, then selects the source, and only writes the access log afterward. The local audit incorrectly says this is clean.  
  Minimum fix: **new frozen run label**. Select the primary source on `calibration_select`, freeze it, then evaluate `final_test` only for that frozen source. Do not generate all-candidate `final_test` appendix rows in the same locked run.

- **[P1] The unlimited reject-option result is mostly a decision-theoretic tautology, and in the primary scenario it collapses to near all-review.**  
  Evidence: the rule explicitly chooses the cheapest of approve/deny/review, and expected cost is evaluated on that same cost surface. In the primary scenario, `cost_aware_reject_option` reviews **99.10%** of cases and is only **0.000194** cheaper than `all_review` in expected cost.  
  Minimum fix: do not claim this as strong empirical dominance. Main-text claim should be: **without capacity constraints, cheap review pushes the rule toward all-review; the empirical contribution is the budgeted frontier, not unrestricted superiority.**

- **[P1] The seven-role split is row-nonoverlapping, but not a clean month-blocked temporal split.**  
  Evidence: the split is row-wise after sorting by timestamp. The output summary shows shared boundary dates across adjacent roles, e.g. `model_dev` ends on `2015-12-01` and `calibration_fit` starts on `2015-12-01`.  
  Minimum fix: either reword this as a **row-wise chronological split with shared boundary months**, or switch to month-grouped cutoffs and rerun.

- **[P2] Calibration-source selection is compliant, but any "best model/calibrator" claim must be narrow.**  
  Evidence: selection on `calibration_select` is correctly pre-registered and executed. But the margin is tiny: `lgbm/sigmoid` Brier `0.1794533` vs `xgb/sigmoid` `0.1794623`. On `final_test`, `xgb/raw` is slightly better by Brier/ECE than the selected source.  
  Minimum fix: say `lgbm/sigmoid` was **selected by rule**, not that it is scientifically superior. Treat the appendix flip as temporal instability, not as permission to switch post hoc.

- **[P2] Venn-Abers and "empirical conformal risk control" remain overclaim traps.**  
  Evidence: the interval artifact explicitly says `implemented_method=empirical_binomial_interval_fallback`. The risk-control baseline is thresholding held-out auto-costs, not formal conformal control, while still labeled `empirical_conformal_risk_control`.  
  Minimum fix: keep both as appendix/baseline diagnostics only. Remove any guarantee language. Prefer renaming in prose to "empirical interval fallback" and "held-out risk-threshold baseline."

- **[P3] This run really did remove the 50k cap for the new main evidence.**  
  Evidence: `tree_max_train_rows` is `null` in `run_config.json`, and the tracker records full-row LR/LGBM/XGB completion.  
  Minimum fix: none for this point. This objection is addressed for `outputs/reject_capacity_full`.

4. **Supported claims and narrowed claims**

Supported:
- The **50k-cap objection is fixed for this run**.
- The **old validation-reuse objection is mostly fixed at row level**: `calibration_fit`, `calibration_select`, `policy_tune`, and `risk_calibration` are separate roles.
- The **primary source was selected on `calibration_select`**, not on `final_test`.
- The **capacity-aware policy yields a monotone cost-capacity frontier** in the primary scenario.
- Standard conformal remains a **baseline**, not the main story.

Narrowed:
- Do **not** claim protocol-clean one-shot final testing.
- Do **not** claim unlimited reject-option cost dominance as a strong empirical discovery.
- Do **not** claim all-review is beaten in any practically important sense under cheap review; in the primary scenario the unrestricted rule is basically all-review.
- Do **not** claim Venn-Abers or formal conformal guarantees.
- Do **not** claim `lgbm/sigmoid` is robustly the best source; only that it was the pre-registered selected source.

5. **Explicit answers**

- `50k cap`: **yes for this run**.
- Validation reuse: **mostly yes at row level**.
- Test-Brier selection: **yes, explicit test-based source selection is removed**.
- Strict locked-test cleanliness: **no**, because all-candidate `final_test` metrics are generated before the source is frozen.
- Seven-role split leakage: **no row leakage found**, but it is **not a strict month-blocked split**.
- Calibration-select source selection: **yes** as a selection rule and recorded output; **no** if interpreted as fully pristine locked-test protocol.
- Final-test-only locked report: **no**, the code touches `final_test` earlier for all calibrators.
- Reject-option and capacity-aware claims: unrestricted reject option only in a narrow structural sense; capacity-aware deferral is supported as a fixed-budget frontier claim.
- Cheap all-review claim boundary: under cheap/high-quality human review, the unconstrained optimum is near all-review; D-CRED's useful contribution is exposing that dependence and offering a budget-constrained review frontier.
- Venn-Abers and empirical conformal risk control: high overclaim risk if prose gets sloppy; keep both as appendix baselines with explicit caveats.

6. **Memory update**

- New P0: the 2026-05-19 reject-capacity rerun still violates its own locked-test story; `final_test` appendix metrics are produced before primary-source freeze.
- New P1: the 50k-cap objection is fixed for `outputs/reject_capacity_full`.
- New P1: explicit test-Brier source selection is fixed, but pristine final-test isolation is not.
- New P1: unlimited reject option is not the paper's empirical win; in the primary scenario it degenerates to 99.1% review and is effectively all-review.
- New P1: seven-way split is row-wise chronological, not month-blocked; boundary-month wording must be narrow.
- New P1: keep Venn-Abers fallback and empirical CRC as appendix-only diagnostics.

</details>

### Debate Transcript (hard mode)

**Author rebuttal.**

- For Weakness 1, partially accepted: the run does not use final-test metrics for source selection, because `selection_metrics` comes from `calibration_select` and `_select_primary_candidate` reads only those metrics. However, the implementation still violates the stronger locked-final-test wording because it computes all-candidate final-test appendix metrics before primary-source selection and writes the final-test access log afterward.
- For Weakness 2, accepted: unrestricted reject option collapses to near all-review and should not be claimed as an empirical dominance result.
- For Weakness 3, accepted with wording clarification: row-level separation is clean, but month-blocked separation is not.
- For Weakness 4, accepted: the selected source is selected-by-rule, not generally best.
- For Weakness 5, accepted: Venn-Abers fallback and empirical CRC must stay appendix/baseline only.

**Reviewer ruling.**

- Weakness 1: **partially accepted**. The rebuttal resolves the accusation of test-Brier selection leakage, but does not resolve the false locked-test wording. Minimum clean fix remains a new frozen rerun with selected-only final-test evaluation. Rewording alone is honest enough for MSc prose, but not enough for a pristine locked-test claim.
- Weakness 2: **accepted**. Resolved if the manuscript adopts capacity-frontier wording.
- Weakness 3: **accepted**. Resolved as a wording issue only unless the thesis keeps claiming clean month-blocked deployment periods.
- Weakness 4: **accepted**.
- Weakness 5: **accepted**.
- Scores unchanged: MSc 8/10, top venue 4/10. Verdict unchanged: MSc almost ready, top venue not ready.

### Actions Taken

- No code changes were made in this review round.
- Recorded the hard-review findings, debate ruling, and updated reviewer memory.

### Results

- The current rerun is MSc-near-ready evidence if claims are narrowed.
- It is not yet defense-clean under the strict locked-final-test wording.
- It is not top-venue-ready: novelty remains modest, the cost model is stylized, and formal risk-control evidence is absent.

### Status

Completed for the reject-option capacity hard review. Recommended next step is a minimum repair pass: selected-only frozen final-test rerun or explicit claim rewording, split wording fix or month-blocked rerun, updated claim audit, and dissertation handoff sync.

## Final Summary - Reject-Option Capacity Rerun

The new `outputs/reject_capacity_full` run materially improves the D-CRED evidence base: it removes the 50k tree cap for the new main evidence, separates calibration fitting/source selection/policy/risk/final roles at row level, and replaces the old conformal-centered claim with a cost-capacity frontier. The central claim should be narrow: D-CRED exposes review-cost and review-capacity trade-offs under stated assumptions; it does not prove unrestricted reject-option superiority, formal Venn-Abers guarantees, or finite-sample conformal risk control. A strict locked-final-test claim still needs either a selected-only rerun under a new frozen label or explicit rewording that final-test appendix metrics were generated in the same reporting run but not used for source selection.

## Round 1 - Reviewer-Response Nightmare Review (2026-05-20T00:16:14+08:00)

### Assessment (Summary)

- MSc score: `6.5-7/10`
- Top-tier ML score: `1.5-2/10`
- Verdict: `almost` for MSc after targeted repair; `not ready` for top-tier ML
- Advisor strict month-blocked experiment: `ready` for dissertation use
- Dean cash-flow experiment: `almost`, but needs a clean rerun or explicit reframing because of the `funded_amnt` predictor/audit contradiction

### Reviewer Raw Response

Full raw responses are preserved in:

- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_BEAUVOIR_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_ERDOS_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_DEBATE_20260520.md`

The consolidated timestamped review is:

- `review-stage/AUTO_REVIEW_20260520_REVIEWER_RESPONSE_NIGHTMARE.md`

### Key Criticisms

- `funded_amnt` is both a cash-flow/outcome component and a model predictor in `scripts/cashflow_feature_acquisition_experiment.py`, while the audit and prose claim it is not a predictor.
- The dean cash-flow model's final-test cash prediction is weak; the tuned cash policy is better interpreted as a realized-policy comparison than as accurate expected-net-cash modeling.
- Predicted VOI selected zero reviews and should remain a negative result.
- Conformal interval review is not universally beneficial across all cost/capacity and loss/profit regimes.
- Older proxy-only dean handoff text is now superseded and should not be cited for the dean story.

### Debate Transcript (nightmare mode)

The author response accepted the `funded_amnt` contradiction as an unresolved blocker, accepted the advisor month-blocked repair as resolved for MSc, partially accepted the dean cash-flow evidence as narrow accepted-loan evidence, and accepted stale proxy-only handoff contamination as a writing blocker.

Reviewer ruling:

- `funded_amnt` contradiction: **accepted**, unresolved.
- Advisor month-blocked temporal critique: **accepted**, resolved for the supervisor's stated MSc-level concern.
- Dean cash-flow claims and review frontier: **partially accepted**; rerun without `funded_amnt` or reframe as post-funding analysis.
- Stale handoff/proxy contamination: **accepted**, unresolved writing risk.

### Actions Taken

- No code changes were made.
- Ran local verification checks against key markdown/CSV/code files.
- Ran `python -m compileall dcred scripts\cashflow_feature_acquisition_experiment.py`, which passed.
- Wrote raw reviewer responses, a trace, reviewer memory update, and a completed review state.

### Results

- The advisor reviewer-response experiment can be integrated as strict temporal robustness evidence.
- The dean reviewer-response experiment should not be integrated as clean final evidence until `funded_amnt` is removed from predictors and the run is regenerated, or the narrative is explicitly reframed.

### Status

Completed. Recommended next step is a focused dean cash-flow repair/rerun and handoff cleanup, not a broad pivot.

## Repair Follow-up - Dean Cash-Flow Clean Rerun (2026-05-20T00:25:13+08:00)

### Actions Taken

- Removed `funded_amnt` from `CHEAP_NUMERIC` in `scripts/cashflow_feature_acquisition_experiment.py`.
- Added a resolver guardrail so `CASHFLOW_COLUMNS` cannot enter numeric predictor groups.
- Reran `python scripts\cashflow_feature_acquisition_experiment.py --run-name dean_cashflow_full --primary-review-cost 10 --seed 42`.
- Updated `refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md`, `DEAN_CASHFLOW_EXPERIMENT_CODE_REVIEW.md`, and `DEAN_CASHFLOW_EXPERIMENT_TRACKER.md`.
- Marked proxy-only dean text as superseded in the writing handoff.

### Results

- `feature_audit_loan_csv.csv` now marks `funded_amnt`, repayment, recovery, and collection-fee fields as `allowed_as_predictor=False`.
- Clean rerun preserves the qualitative result: tuned cash policy beats tuned PD on realized utility; conformal interval review remains the strongest non-oracle acquisition rule; predicted VOI selects zero reviews.
- Key clean-rerun numbers: tuned cash `-25.96` mean utility at `0.74%` approval; tuned PD `-109.12`; conformal interval review lift `+28.57` at 5% review and `+27.10` at 10% review under $10 review cost.

### Status

The `funded_amnt` blocker is repaired locally and the experiment has been rerun. External nightmare re-review has not yet been rerun; the safe claim remains the narrowed accepted-loan cash-flow decision-analysis claim.

## Round 1 - Blind-Review Response Nightmare Audit (2026-05-20T23:20:00+08:00)

### Assessment (Summary)

- Score: `6.8/10` MSc from the primary reviewer; `6.5/10` MSc from the fresh adversarial verifier.
- Top-tier score: `1.8/10` and `1.5/10`.
- Verdict after debate: `almost / limited ready` for MSc thesis writing only after claim-control downgrade; not ready as a claim that the blind-review points are fully closed.

### Reviewer Raw Responses

Raw responses are preserved in:

- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_ROUND1_CONFUCIUS_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_ROUND1_KANT_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_DEBATE_20260520.md`

### Key Criticisms

- `locked_final_protocol` is a retrospective selected-only wrapper around existing source runs, not a true frozen-config rerun.
- `dcred_layer_ablation_table.csv` is a stitched narrative summary across different populations and source runs, not a controlled single-protocol ablation.
- Cash-flow remains a negative/mixed result: all deployable approval-constrained policies have negative utility and PD ranking is selected at every target approval rate.
- Capacity frontier evidence should be written as a trade-off, not dominance over matched baselines; some baselines are not truly capacity-matched.
- Responsible-credit and feature audit outputs are risk-exposure / header-catalog / capped-sanity evidence only.

### Debate Transcript

The executor accepted the three main objections and proposed downscoped wording. The reviewer ruled:

- `locked_final_protocol`: accepted; resolved for MSc writing only as limitation/disclosure, not as closure of blind-review Point 2.
- cash-flow negative result: accepted; resolved for MSc writing if A5 and the cash-flow section are rewritten as negative/mixed decision analysis.
- responsible-credit / feature audit: partially accepted; acceptable as appendix/limitation evidence, not as closure of Points 8/11.

### Actions Taken

- Wrote raw reviewer responses and trace files.
- Appended reviewer memory with the blind-review response concerns.
- Wrote `review-stage/CLAIMS_FROM_RESULTS_BLIND_REVIEW_NIGHTMARE_20260520.md`.
- Updated `review-stage/REVIEW_STATE.json` with completed state and unresolved blockers.

### Status

Completed for this review pass. The next action is claim-control and handoff synchronization. Further experiments are needed only if the thesis must claim full closure of the blind-review points rather than limited MSc readiness.

## Round 2 - Closure-Safe Blind-Review Nightmare Re-Review (2026-05-20T23:56:00+08:00)

### Assessment (Summary)

- Primary memory reviewer: MSc `8.2/10`, top-tier ML `2.3/10`.
- Fresh adversarial verifier: MSc `8/10`, top-tier ML `3/10`.
- Verdict: experiment/reviewer-response loop can stop as expert-recognized for MSc claim-controlled writing.
- Remaining gate: BR704 thesis-text claim audit after integration.

### Reviewer Raw Responses

Raw responses are preserved in:

- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_CLOSURE_SAFE_GALILEO_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_CLOSURE_SAFE_LEIBNIZ_20260520.md`

Trace:

- `review-stage/TRACE_BLIND_REVIEW_CLOSURE_SAFE_NIGHTMARE_20260520.md`

### Key Rulings

- The true pre-run frozen selected-only rerun is accepted for MSc-level locked-final hygiene.
- Capacity evidence is MSc-usable as conditional, CI-aware capacity allocation evidence, not algorithmic dominance.
- Responsible-credit evidence is acceptable as risk-exposure audit only.
- Feature stress is acceptable as deterministic 50k-row same-model capped evidence only.
- Cash-flow remains negative/mixed and must be written as accepted-loan decision analysis, not a deployable cash-model win.

### Actions Taken

- Added resource safety guardrails to `scripts/blind_review_response_experiments.py`: full-data stress is refused without an explicit dangerous flag, LGBM stress defaults to bounded parallelism, deterministic sample spans the full CSV, and a progress log is written.
- Regenerated `outputs/blind_review_response_20260520-closure_safe/` and `outputs/blind_review_response_latest/`.
- Renamed `allowed_expanded` in `all_fields_feature_audit.csv` to `included_expanded_stress`.
- Reworded the result summary to state the selected-only evidence is from the true pre-run frozen month-blocked selected source.
- Synced the closure-safe pack and claim-control file into `paper_writing_handoff_20260511/`.
- Wrote `review-stage/FINAL_CLAIM_GREP_AUDIT_BLIND_REVIEW_CLOSURE_20260520.md`.

### Results

- The experiment loop has reached expert recognition for MSc claim-controlled writing.
- No further major experiment is required unless the thesis audit finds overclaiming or the supervisor asks a new empirical question.

### Status

Completed. BR704 remains a later writing-stage audit after thesis integration.
