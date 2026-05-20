# Dean Cash-Flow Experiment Code Review

Date: 2026-05-20

This timestamped code review records the reviewer-triggered clean rerun after removing `funded_amnt` from predictor groups.

Checks passed:

- `python -m compileall scripts\cashflow_feature_acquisition_experiment.py`
- full rerun of `python scripts\cashflow_feature_acquisition_experiment.py --run-name dean_cashflow_full --primary-review-cost 10 --seed 42`
- `feature_audit_loan_csv.csv` now marks `funded_amnt`, repayment, recovery, and collection-fee fields as `allowed_as_predictor=False`
- month boundary audit remains clean with 139 `OK_NO_SHARED_MONTH` rows

Residual risks are unchanged: accepted-loan-only scope, no real human reviewer, weak cash regression under drift, and regime-dependent review benefit.
