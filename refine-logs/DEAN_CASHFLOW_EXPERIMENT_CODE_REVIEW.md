# Dean Cash-Flow Experiment Code Review

Date: 2026-05-20

Scope:

- `scripts/cashflow_feature_acquisition_experiment.py`
- outputs in `outputs/dean_cashflow_full/`
- reviewer-triggered repair: remove `funded_amnt` from predictors and rerun full experiment.

## Checks

| Check | Status | Notes |
|---|---|---|
| Syntax/import check | PASS | `python -m compileall scripts\cashflow_feature_acquisition_experiment.py` passed after the repair. |
| Full run completion | PASS | `python scripts\cashflow_feature_acquisition_experiment.py --run-name dean_cashflow_full --primary-review-cost 10 --seed 42` completed. |
| `funded_amnt` contradiction fix | PASS | `funded_amnt` is still used in `net_cash`, but removed from `CHEAP_NUMERIC` and excluded from predictor groups by resolver guardrails. |
| Cash-flow field handling | PASS | `feature_audit_loan_csv.csv` marks `funded_amnt`, repayment, recovery, and collection-fee fields as `allowed_as_predictor=False`. |
| Censored loan handling | PASS | Non-terminal statuses are excluded from main evaluation. |
| Temporal split | PASS | Month-blocked roles are written; final test is 2017-11 to 2018-12; month audit has 139 `OK_NO_SHARED_MONTH` rows. |
| Feature availability warning | PASS WITH CAVEAT | sklearn skipped all-missing full numeric fields such as `open_acc_6m` in the training split. This is documented as a feature-availability limitation. |
| Negative result preservation | PASS | Predicted VOI selecting zero reviews is still reported as a negative result. |
| Cost-sensitivity wording | PASS WITH CAVEAT | Conformal review is positive at $5-$100 for 5%, 10%, and 20% capacities, but turns negative at high cost and 30%-50% capacities. |

## Residual Risks

- This evaluates accepted/funded loans only and cannot identify rejected-applicant outcomes.
- Review is modeled as acquisition of additional features, not as a real human judgment process.
- Cash-flow regression remains difficult under temporal drift; the report should emphasize decision utility and calibration boundaries rather than claiming a universally accurate profit model.
- The review-feature bundle still needs careful prose because operational fields such as `verification_status` and `initial_list_status` are proxies for acquired information, not proof of a real bank workflow.
