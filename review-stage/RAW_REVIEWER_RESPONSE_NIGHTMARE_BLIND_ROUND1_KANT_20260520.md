# Raw Reviewer Response - Blind Review Nightmare Round 1 - Kant

Reviewer: fresh adversarial repository verifier
Date: 2026-05-20

## Score

MSc dissertation: `6.5/10`

Top-tier ML venue: `1.5/10`

## Verdict

The `blind_review_response_latest` package is better understood as evidence-hygiene and claim-narrowing work, not as a true locked rerun that closes the blind-review concerns. It can support a narrower and more honest MSc defense narrative, but it cannot support claims that final-test is pristine, cash-flow is deployable, responsible-credit/fairness has been covered, or feature audit is complete.

## Direct Verification Findings

1. `locked_final_protocol` is not a pristine pre-registered final rerun. The plan itself says the locked claim is invalid if the config is written after the run. The tracker marks `BR201 = DONE_REUSED`. The script reads old `selected_probability_predictions.csv` and `final_decision_results.csv`, then writes `frozen_config.yaml` and `selected_only_final_decision_report.csv`. The protocol manifest was created at `2026-05-20 22:34`, while the source `reject_capacity_month_blocked` files were modified at `2026-05-19 22:19`.

2. `dcred_layer_ablation_table.csv` is stitched across old directories, not a controlled single-protocol ablation. A0/A1 come from `outputs/full/lending_random_vs_temporal.csv`; A3/A4 come from `reject_capacity_month_blocked/capacity_frontier.csv`; A5 comes from `dean_cashflow_full/utility_approval_frontier.csv`. A0/A1 use 269,537 test rows, whereas the locked final probability table uses 66,205 rows.

3. Cash-flow has no deployable positive-utility policy. `cashflow_coverage_constrained_best_policy.csv` selects `pd_risk_ranking` at all seven approval targets, and all selected deployable `mean_net_cash_per_app` values are negative. The full frontier also has all deployable policies negative at 1% approval, with only the oracle upper bound positive. `cashflow_model_metrics.csv` keeps negative final-test cash R2.

4. The primary cost scenario still collapses toward near-all-review. In `selected_only_final_decision_report.csv`, all-review expected cost is `0.16197`; cost-aware reject-option expected cost is `0.16181`, but with `0.99169` review rate and `0.00831` approval rate. The break-even table also gives about `0.99169` review-beneficial share under the primary scenario.

5. Some entries in `matched_capacity_frontier_with_ci.csv` are not actually matched. The empirical-risk rows at nominal 0.2, 0.3, and 0.5 capacity all use the same actual `0.190227...` capacity and the same costs. The oracle 0.5 row actually reviews only `0.407688...`. The empirical-risk baseline is implemented with a fixed 0.80 quantile risk threshold, and `BR305` remains `PARTIAL`.

6. `responsible_credit_audit.csv` is only a proxy-group exposure table. The script groups by `addr_state`, `zip3`, `home_ownership_n`, `revenue_decile`, `loan_amnt_decile`, and `purpose`; output columns lack disparate-impact analysis, utility/cost, protected-class inference, or legal compliance evidence. Small-cell rows are flagged but not actually suppressed.

7. Feature audit is heuristic header labeling, not a systematic provenance audit. The script classifies by field-name rules. Many accepted-loan fields use the generic reason `candidate application/review field`, which supports a field catalog but not a field-level semantic audit.

8. Strict/default/expanded stress is row-capped sanity and switches model class. The file says `stress_scope=sanity_cap`, `rows_used=400000`, and `final_test_rows=22457`. The script uses `SGDClassifier`, not the locked final `lgbm/sigmoid` model.

## Top Blockers And Minimum Fixes

1. Rename/reframe `locked_final_protocol` as a retrospective wrapper around the 2026-05-19 month-blocked selected run, unless a real frozen-config rerun is executed.

2. Downgrade `dcred_layer_ablation_table.csv` to a stitched evidence summary. A real layer ablation would need one protocol, split, and evaluation population.

3. Rewrite cash-flow: current deployable policies all have negative utility; the safe claim is only accepted-loan approval-constrained frontier analysis.

4. Do not call the frontier `matched` unless empirical-risk, oracle, and uncertainty rows are truly aligned to target capacities and monthly stability is complete.

5. Rename responsible-credit audit as risk-exposure audit, perform real suppression or aggregation, and avoid fairness-compliance wording.

6. Describe feature work as a header-level catalog plus capped sanity stress unless a full-data same-model rerun exists.

## Safe Claims

- A strict month-blocked selected source run exists and can be used as classification/capacity continuity evidence.
- The selected `lgbm/sigmoid` source has reportable final-test calibration quality, including Brier `0.1305` and ECE `0.0107`.
- Under stylized costs, capacity-aware review lowers expected/realized cost versus no-review.
- Review value is highly cost- and residual-error-dependent, and the primary scenario is near all-review.
- Cash-flow supports accepted/funded-loan policy analysis only, not profitable deployable policy.
- Responsible-credit supports proxy-group risk exposure only.
- Feature control supports a field catalog and sanity stress, not complete provenance audit.

## Must Not Claim

- Pristine locked final test or pre-registered rerun.
- Blind-review Point 2 fully closed.
- Cash-flow model or cash ranking is profitable/deployable.
- Matched frontier proves D-CRED allocation dominates baselines.
- Strict/default/expanded proves full-data leakage robustness.
- Responsible-credit audit demonstrates fairness compliance or absence of disparate impact.
- Feature audit is a complete systematic field-level audit.
- Capacity frontier monotonic decline itself is an empirical discovery.

## Memory Update

The verifier recommended recording: `locked_final_protocol` is a retrospective wrapper; deployable cash-flow frontier is all negative; zip/feature audit is sanity-level rather than full-data proof.
