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
