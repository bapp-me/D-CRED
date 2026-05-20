# Raw Reviewer Response - Nightmare Round 1 - Erdos

Reviewer agent id: `019e40f3-aa05-77a3-be41-9b39e5c1928f`

1. **Advisor critique verdict**

Addressed for the core critique.

- The advisor asked for a strict month-blocked seven-role rerun with `month_boundary_audit.csv` and a row-vs-month comparison in [导师review.md](/D:/code/diss_codex/导师review.md:5).
- The repo now has a true month-blocked splitter in [splits.py](/D:/code/diss_codex/D-CRED/dcred/splits.py:98), the reject-capacity pipeline calls it in [experiment.py](/D:/code/diss_codex/D-CRED/dcred/experiment.py:287), and the frozen protocol says `final_test` is not used for selection and reporting is `selected_only` in [selection_protocol.md](/D:/code/diss_codex/D-CRED/outputs/reject_capacity_month_blocked/selection_protocol.md:16).
- The run shows 139 months with no shared role, same selected source `lgbm/sigmoid`, and a monotone capacity frontier in [ADVISOR_REVIEW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/ADVISOR_REVIEW_EXPERIMENT_RESULTS.md:26) and [EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/outputs/reject_capacity_month_blocked/EXPERIMENT_RESULTS.md:24).
- Rolling-window was not added, but the advisor explicitly framed month-blocked rerun as the minimum necessary fix in [导师review.md](/D:/code/diss_codex/导师review.md:25).

2. **Dean critique verdict**

Partially addressed, not fully closed.

- The repo now uses the downloaded `loan.csv` with real repayment columns and a month-blocked accepted-loan run, as claimed in [DEAN_CASHFLOW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md:21).
- On final test, tuned cash beats fixed and tuned PD on mean realized utility, but only by becoming extremely conservative: `-24.07` utility per app at `0.71%` approval versus tuned PD `-109.06` at `30.10%` approval in [economic_utility_decisions.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/economic_utility_decisions.csv:3).
- Full features improve over cheap features on final-test PD and cash error in [model_metrics.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/model_metrics.csv:6).
- The best non-oracle review rule in this run is conformal-style review, while predicted VOI selects zero reviews, in [feature_acquisition_frontier.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/feature_acquisition_frontier.csv:18).
- But the experiment is still funded-loan-only, not reject inference, not real human review, and not causal deployment ROI, as the repo itself admits in [DEAN_CASHFLOW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md:125).

3. **Fatal leakage or protocol issues**

No fatal temporal leakage found in the advisor rerun.

One serious dean-side protocol contradiction remains:

- The writeups say cash-flow fields are outcome-only and not predictors in [DEAN_CASHFLOW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md:43) and [DEAN_CASHFLOW_WRITING_UPDATE_20260519.md](/D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260519.md:22).
- The audit CSV also marks `funded_amnt` as disallowed in [feature_audit_loan_csv.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/feature_audit_loan_csv.csv:5).
- But the actual code includes `funded_amnt` in `CHEAP_NUMERIC` in [cashflow_feature_acquisition_experiment.py](/D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:54), carries it into `cheap_numeric` and `full_numeric` in [cashflow_feature_acquisition_experiment.py](/D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:207), and trains the cheap/full/VOI models on those lists in [cashflow_feature_acquisition_experiment.py](/D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:339) and [cashflow_feature_acquisition_experiment.py](/D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:420).
- I do not classify this as proven catastrophic outcome leakage, because a raw-file scan shows `funded_amnt == loan_amnt` for 99.91% of rows. But the current claim "cash-flow fields are not predictors" is false as written, and that is a real blocker.

One claim-level overstatement also exists:

- [DEAN_CASHFLOW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md:104) says conformal review stays positive across review costs `$5-$100`.
- Actual output turns negative at higher capacities, e.g. 30% and 50% capacity with `$100` review cost in [review_cost_sensitivity.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/review_cost_sensitivity.csv:175).

4. **Claim-control guidance**

Can write:

- Month-blocked temporal isolation fixes the advisor's specific protocol complaint and leaves the main capacity-frontier story qualitatively unchanged.
- The unrestricted reject option still degenerates to near all-review, so the practical result is the capacity-aware frontier, not reject-option dominance.
- Observed repayment-based net cash on accepted/funded loans changes the objective materially relative to binary default cost.
- Tuned cash-flow policy beats fixed and tuned PD on mean realized utility, but with a very low approval rate and large opportunity cost.
- Full-feature review bundle improves prediction quality, and conformal-style review is the strongest non-oracle acquisition rule in this run.
- Predicted VOI is a negative result and should stay negative.

Cannot write:

- That all cash-flow fields were excluded from predictors.
- Full applicant-pool approve/deny claims, reject inference, real human reviewer superiority, or FICO-specific claims.
- That conformal review is positive across the full tested cost-capacity grid.
- That predicted VOI is the winning method.
- That the cash model is accurate in a strong sense; final-test cash `R^2` is still negative in [model_metrics.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/model_metrics.csv:6).

5. **Scores**

- MSc readiness: `6.5/10` current state.
- Top-tier venue readiness: `1.5/10`.

Reason: the advisor repair is good enough for an MSc defense, but the dean experiment still has a dirty audit trail, narrow scope, weak cash prediction, and limited novelty.

6. **Ranked blockers and minimum fixes**

1. Fix the `funded_amnt` contradiction.
   Minimum safe fix: remove `funded_amnt` from predictor lists, rerun `dean_cashflow_full`, regenerate the audit CSV and markdown, and confirm conclusions survive.

2. Stop stale proxy-only dean files from being cited.
   [ADVISOR_REVIEW_EXPERIMENT_RESULTS.md](/D:/code/diss_codex/D-CRED/refine-logs/ADVISOR_REVIEW_EXPERIMENT_RESULTS.md:13) and [ADVISOR_REVIEW_WRITING_UPDATE_20260519.md](/D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/ADVISOR_REVIEW_WRITING_UPDATE_20260519.md:40) are now obsolete for the dean story.

3. Tighten the dean review-cost and ratio prose.
   "Positive across `$5-$100`" must be narrowed to low-to-moderate capacities; 5.0 loss/profit ratio at 10% is slightly negative in [loss_profit_ratio_sensitivity.csv](/D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/loss_profit_ratio_sensitivity.csv:36).

4. Keep the funded-loan-only and low-approval caveats in main text, not buried in appendix.

7. **Memory update**

Unresolved suspicions:

- `funded_amnt` is probably acting as a near-duplicate of `loan_amnt`, not a dramatic hidden leakage channel, but the repo has not proven that results are robust once it is removed.
- The review-feature bundle includes operational fields such as `verification_status` and `initial_list_status`; the repo does not fully prove these map cleanly to a real acquisition stage.
- Stale proxy-era files remain in the repo and can easily contaminate later writing if someone cites the wrong handoff note.
- The dean experiment is good evidence for funded-loan utility ranking, not yet for full bank decisioning over the true applicant pool.
