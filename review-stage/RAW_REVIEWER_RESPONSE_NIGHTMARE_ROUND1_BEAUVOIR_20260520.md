# Raw Reviewer Response - Nightmare Round 1 - Beauvoir

Reviewer agent id: `019e40f3-a991-7d83-82ad-4d33e4055deb`

**Findings**

1. The dean-response bundle currently breaks its own clean feature-separation claim. In [cashflow_feature_acquisition_experiment.py](</D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:54>), `funded_amnt` is included in `CHEAP_NUMERIC`, and [the resolver](</D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:207>) passes it into the actual predictor set. But the same script's [audit writer](</D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:906>) and the emitted [feature_audit_loan_csv.csv](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/feature_audit_loan_csv.csv:5>) label `funded_amnt` as `outcome_or_post_origination, False`, and the writing update repeats "outcome labels only, never as application-time predictors" in [DEAN_CASHFLOW_WRITING_UPDATE_20260519.md](</D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260519.md:24>). I also checked `loan.csv`: `funded_amnt != loan_amnt` in 2,062 of 1,306,387 terminal rows, so this is not purely cosmetic.

2. The dean cash-flow run supports realized policy comparison, but not a strong "predict expected net cash" story. Final-test cash regression quality is poor in [model_metrics.csv](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/model_metrics.csv:6>): cheap/full cash `R^2 = -0.5708 / -0.4824`, with MAE `4076.8 / 3786.1`. That shows up in policy behavior: the direct cash rule approves `99.96%` of loans and loses `-1670.24` per app, while the tuned cash rule only works by collapsing approvals to `0.71%` and still leaves `650.23` rejected-profitable opportunity cost per app in [economic_utility_decisions.csv](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/economic_utility_decisions.csv:2>).

3. The learned VOI/acquisition claim is not established. In the final frontier, predicted VOI reviews literally `0%` of cases at `5%`, `10%`, `20%`, and `50%` capacity in [EXPERIMENT_RESULTS.md](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/EXPERIMENT_RESULTS.md:31>). The only non-oracle winner is conformal interval review. Worse, the VOI learner is trained on model-predicted gross value, not realized incremental utility: see [cashflow_feature_acquisition_experiment.py](</D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:404>). That makes the negative VOI result informative, but weaker than a true realized-VOI test.

4. The dean response is only partially robust to cost assumptions. Conformal review is positive under the primary high-loss regime, but the loss/profit sensitivity table in [EXPERIMENT_RESULTS.md](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/EXPERIMENT_RESULTS.md:94>) is negative at ratios `1`, `2`, and essentially flat at `5`; it only turns meaningfully positive around `10x` loss asymmetry and above. So "review helps under realistic cost grids" is too broad. The defensible claim is narrower: conformal-style review helps when downside losses materially dominate upside gains.

5. The advisor month-blocked rerun does substantially answer the supervisor critique. The month audit is clean (`139/139` months are `OK_NO_SHARED_MONTH`), the selected source stays `lgbm/sigmoid`, and row-vs-month deltas are tiny: no-review expected cost `0.619721` vs `0.621649`, 5% capacity `0.587459` vs `0.589390`. See [reject_capacity_month_blocked/EXPERIMENT_RESULTS.md](</D:/code/diss_codex/D-CRED/outputs/reject_capacity_month_blocked/EXPERIMENT_RESULTS.md:28>) and [ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv](</D:/code/diss_codex/D-CRED/refine-logs/ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv>). The caveat remains the same: unrestricted reject option still degenerates to `99.17%` review, so the claim must stay on the capacity frontier, not reject-option superiority.

**Scores**

MSc dissertation readiness: `7/10`
Top-tier ML venue readiness: `2/10`

**Verdict**

Advisor-response group: `ready` for dissertation use.
Dean-response group: `almost` for dissertation use, `not ready` for top-tier ML.
Overall: `almost` ready for MSc defense, `not ready` for a top-tier ML venue.

**Minimum fixes**

MSc required:

1. Remove `funded_amnt` from predictors and rerun the dean cash-flow experiment, or explicitly reframe the task as post-funding analysis rather than application-time decisioning.
2. Tighten the dean-side claim to: observed cash-flow utility on accepted loans, month-blocked evaluation, tuned cash policy beats PD thresholds under this objective, and conformal review is the best non-oracle review rule here. No stronger claim.
3. Clean the writing handoff so the superseded proxy-only dean narrative in [ADVISOR_REVIEW_WRITING_UPDATE_20260519.md](</D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/ADVISOR_REVIEW_WRITING_UPDATE_20260519.md:31>) cannot coexist with the newer cash-flow narrative in [DEAN_CASHFLOW_WRITING_UPDATE_20260519.md](</D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260519.md:5>).
4. Add one explicit limitation paragraph on the tuned cash policy's `0.71%` approval rate and very high missed-profit cost.

Top-venue required:

1. Rebuild the dean experiment with leakage-clean features and a VOI target tied to realized incremental utility, not predicted gross value.
2. Add stronger review baselines, especially threshold-proximity review around the tuned decision boundary; current "uncertainty_review" is not a strong matched baseline.
3. Add rolling-window or multiple temporal backtests, plus another dataset or setting. One accepted-loan book with one blocked horizon is not enough.
4. Address accepted-loan selection bias directly, or narrow the paper to funded-loan policy evaluation rather than general credit approval decisioning.

**Memory update**

- Persistent suspicion: dean cash-flow evidence currently contains a feature-separation inconsistency around `funded_amnt`.
- Unresolved concern: expected utility modeling is badly drifted; realized-policy comparison is safer than any claim about accurate net-cash prediction.
- Claim boundary: safe MSc framing is a deployment-oriented credit-risk evaluation and decisioning framework on accepted loans, not a new ML algorithm and not a winning learned VOI method.
- Claim boundary: the advisor-response month-blocked frontier is solid; the dean-response cash-flow experiment is useful but still a constrained, caveated extension.
