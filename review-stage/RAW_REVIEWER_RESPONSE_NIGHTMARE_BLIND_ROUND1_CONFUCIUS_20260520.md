# Raw Reviewer Response - Blind Review Nightmare Round 1 - Confucius

Reviewer: primary memory-carrying nightmare reviewer
Date: 2026-05-20

## Score

MSc dissertation: `6.8/10`

Top-tier ML venue: `1.8/10`

## Verdict

`not ready` for MSc blind-review response.

## Critical Weaknesses

1. `locked_final_protocol` is not a post-freeze rerun; it is a retrospective package around older runs. Evidence cited by the reviewer includes `frozen_config.yaml`, `protocol_manifest.json`, and `BLIND_REVIEW_EXPERIMENT_TRACKER.md`, where `BR201/BR202` are `DONE_REUSED`. The month-blocked source run is cleaner than the row-wise run, but this still does not satisfy the expert's requested "freeze first, then run final_test" protocol.

2. The responsible-credit audit is too shallow for strong deployment-oriented wording. `responsible_credit_audit.csv` contains default-rate, Brier, ECE, approval, rejection, and review rates, but lacks policy-conditioned utility or realized cost and lacks a direct full-data with-zip versus without-zip output. The reviewer also flagged heavy zip3 small-cell suppression.

3. The cash-flow layer remains a negative result, but `dcred_layer_ablation_table.csv` compresses it into something that can look like a contribution layer. `cashflow_coverage_constrained_best_policy.csv` selects `pd_risk_ranking` at all approval targets and all deployable mean net-cash values are negative; `cashflow_model_metrics.csv` keeps negative final-test `cash_r2`.

4. The capacity frontier now addresses the expert's requested format, but it does not establish strong empirical superiority over baselines. D-CRED versus uncertainty realized-cost differences are very small at 1%, 2%, 5%, and 10% capacity, with overlapping confidence intervals. The empirical-risk baseline is partly degenerate above 20% capacity, and monthly stability remains `PARTIAL`.

5. The feature-audit stress test is sanity-level evidence, not blind-review closure. The results summary admits strict/default/expanded stress uses a deterministic 400k row cap, and the stress CSV has only 22,457 final-test rows.

6. The blind-review response package is not integrated into the writing handoff or final claim-control state. The handoff README still says the blind-review files are a plan rather than completed results, while `BR703` and `BR704` remain pending.

## Minimum Fixes

Must fix before thesis:

- Either run a genuine post-freeze locked rerun, or reframe the current `locked_final_protocol` as a retrospective selected-only audit and stop implying a new pristine rerun.
- Rewrite cash-flow claims so the main result is "cash model weak; under matched approval, PD ranking is consistently best among deployable policies." A5 must not look like a positive contribution.
- Add a direct full-data with-zip versus without-zip table with policy-conditioned approved-default, utility, and realized-cost columns, or remove strong language that Point 8 is answered.
- Complete claim-control and handoff synchronization before calling the blind-review response ready.

Can write as limitation:

- Capacity frontier may be written as a comparative trade-off, not as stable superiority over uncertainty.
- Empirical/conformal baselines are conservative references only.
- zip3 results are exploratory because small-cell suppression is heavy.
- Cash-flow is accepted/funded-loan decision analysis only, not applicant-pool reject inference.

## Expert Point Status

Genuinely addressed:

- Point 4: cost assumptions are now exposed through grid, break-even table, and near-all-review region map.
- Point 6: cash-flow critique is addressed in analysis form, but the result is negative.

Partially addressed:

- Point 1: ablation table exists, but not as a clean single-protocol layer study.
- Point 2: selected-only month-blocked evidence exists, but not a new locked rerun.
- Point 3: CI/baseline frontier exists, but superiority evidence is weak and some baselines degenerate.
- Point 8: subgroup audit exists, but not a direct zip/proxy policy audit.
- Point 11: all-field catalog exists, but strict/default/expanded remains sanity-scale.

Not addressed:

- No point is completely blank, but Points 2, 8, and 11 do not meet closure standard.

## Debate Hooks

1. If the author argues that the 2026-05-19 month-blocked run was already frozen, acceptable evidence would require freeze artifacts with undeniable timestamps before the source run and logs proving final-test invisibility.

2. If the author argues that responsible-credit only promises risk exposure, acceptable evidence still requires at least a full-data `default` versus `no-zip` comparison with policy-conditioned utility or realized cost.

3. If the author argues cash-flow is about frontier change rather than winning, acceptable evidence is either a cash/hybrid win at an approval target with reasonable uncertainty or an explicit downgrade to negative-result decision analysis.

## Memory Update

```markdown
## Round 2 - Blind-Review Response Bundle - Score: 1.8/10 top venue, 6.8/10 MSc

- **Resolved partially**: The blind-review bundle now contains real artifacts for cost sensitivity, capacity CI/baselines, cash-flow approval frontier, responsible-credit audit, and all-field audit.
- **New P0**: `locked_final_protocol` is not a true frozen rerun; tracker marks BR201/BR202 as `DONE_REUSED`, and the 2026-05-20 package points back to pre-existing 2026-05-19/2026-05-20 source runs.
- **Unresolved claim risk**: The cash-flow layer is still a negative result. `cashflow_coverage_constrained_best_policy.csv` selects `pd_risk_ranking` at every approval target, and all deployable mean net cash values remain negative.
- **Unresolved claim risk**: The capacity frontier is better framed now, but D-CRED does not cleanly separate from uncertainty at the CI level; empirical-risk baseline is partly degenerate above 20% capacity.
- **Unresolved claim risk**: The responsible-credit audit is too shallow for strong deployment-oriented wording. It lacks direct with/without-zip outputs and policy-conditioned utility/realized-cost columns; most `zip3` rows are small-cell suppressed.
- **Unresolved disclosure**: The strict/default/expanded feature stress test is only a 400k-row sanity cap and should not be sold as a full-data blind-review closure.
- **Process risk**: BR703/BR704 remain pending, and the handoff README is stale relative to the new blind-review outputs.
```
