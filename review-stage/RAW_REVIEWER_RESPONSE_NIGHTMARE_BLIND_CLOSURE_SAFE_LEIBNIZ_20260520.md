# Raw Reviewer Response - Leibniz

Date: 2026-05-20
Mode: fresh independent nightmare reviewer
Agent id: 019e4612-2c55-77d0-a26d-9bead35d8b49

I inspected the named artifacts directly.

**Verdict**

Almost ready for the MSc blind-review response. Experimental closure is now largely acceptable; the remaining risk is claim integration, not another major experiment.

Scores:
- MSc dissertation readiness: **8/10**
- Top-tier ML readiness: **3/10**

**Key Evidence**

The locked rerun is materially credible now: `frozen_config.yaml` records a pre-run frozen protocol, month-blocked split, selected-only final reporting, and no all-candidate final appendix. The response manifest explicitly grades this as `true_pre_run_freeze` and records hashes for the freeze, month audit, and predictions. Final test is 66,205 rows, one-shot locked final report only.

Capacity evidence is now capacity-aligned and includes CI/baselines. At 10% review, D-CRED improves no-review realized cost `0.618 -> 0.553`, beats random `0.571`, and narrowly beats uncertainty `0.556`, but uncertainty CI overlaps and all-review remains much cheaper at `0.162`.

Cash-flow remains a negative/mixed result. Final-test cash R2 is still negative (`-0.487` full model), and the constrained best policy is PD ranking at all approval targets with negative mean net cash. This is acceptable only as a limitation-bearing decision-analysis result.

Responsible-credit and feature control are now present but bounded: subgroup audit has policy-conditioned cost and suppression, group rules suppress cells under 200, and feature stress is explicitly row-capped at 50k with only 2,447 final rows. The handoff sync appears exact: 26/26 response-pack files hash-match in the handoff, and the dated claim-control file hash matches.

**Remaining Weaknesses**

1. **Thesis integration is not complete.** Tracker says thesis table map is partial and final claim audit is pending. Evidence pack is ready; thesis/response text still needs audit.
2. **Cash-flow cannot be sold as a win.** It is a negative result with weak cash regression and PD ranking dominating deployable policies.
3. **Capacity claim must stay conditional.** It supports capacity-limited allocation under stated costs, not "D-CRED dominates"; all-review and near-all-review regions remain strong caveats.
4. **Feature stress is capped sanity evidence.** Same-model 50k-row stress is useful, not definitive full-data leakage/proxy validation.
5. **Responsible-credit is exposure audit only.** No legal compliance, no reject-inference solution, no causal fairness claim.
6. **A0/A1 ablation is still stitched historical evidence.** Same-protocol evidence exists for the selected final-test decision comparison, but not the whole contribution ladder.

**Minimum Fix**

No new major experiment is required for MSc-level `expert认可`. The loop can stop **after** writing integration and a final claim audit: explicitly state the cash-flow negative result, capacity conditionality, feature-stress cap, responsible-credit limits, and stitched-vs-same-protocol ablation boundary.
