# Dean Cash-Flow Experiment Code Review

Date: 2026-05-19

Scope:

- `scripts/cashflow_feature_acquisition_experiment.py`
- outputs in `outputs/dean_cashflow_full/`

## Checks

| Check | Status | Notes |
|---|---|---|
| Syntax/import check | PASS | `python -m compileall scripts\cashflow_feature_acquisition_experiment.py` passed. |
| Full run completion | PASS | `python scripts\cashflow_feature_acquisition_experiment.py --run-name dean_cashflow_full --primary-review-cost 10 --seed 42` completed. |
| Cash-flow field handling | PASS | Repayment fields are used to construct `net_cash` only; they are excluded from predictors in `feature_audit_loan_csv.csv`. |
| Censored loan handling | PASS | Non-terminal statuses are excluded from main evaluation. |
| Temporal split | PASS | Month-blocked roles are written; final test is 2017-11 to 2018-12. |
| Feature availability warning | PASS WITH CAVEAT | sklearn skipped all-missing full numeric fields such as `open_acc_6m` in the training split. This is documented as a feature-availability limitation. |
| Negative result preservation | PASS | Predicted VOI selecting zero reviews is reported as a negative result. |

## Residual Risks

- This evaluates accepted/funded loans only and cannot identify rejected-applicant outcomes.
- Review is modeled as acquisition of additional features, not as a real human judgment process.
- Cash-flow regression remains difficult under temporal drift; the report should emphasize decision utility and calibration boundaries rather than claiming a universally accurate profit model.
