# Dean Cash-Flow Experiment Results

Date: 2026-05-20

Primary run:

- `outputs/dean_cashflow_full/`
- implementation: `scripts/cashflow_feature_acquisition_experiment.py`
- raw data: `data/raw/lending_club/loan.csv`
- repair: removed `funded_amnt` from predictor groups after the nightmare reviewer found it was both a cash-flow component and a cheap predictor.

This timestamped result summary is the same as the fixed latest file `refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md`.

## Executive Conclusion

The clean rerun preserves the qualitative dean-response conclusions: tuned cash-flow policy beats fixed/tuned PD thresholds on final-test realized utility, conformal interval review is the strongest non-oracle acquisition rule, and predicted VOI remains a negative result selecting zero reviews.

Key clean-rerun numbers:

- Fixed PD threshold 0.5: mean utility -524.14, approval 65.35%.
- Tuned PD threshold: -109.12, approval 29.86%.
- Tuned cash model: -25.96, approval 0.74%.
- No-review cheap model: -53.74.
- All-review full model: -35.96.
- Conformal interval review at 5% capacity and $10 cost: -25.16, lift +28.57.
- Conformal interval review at 10% capacity and $10 cost: -26.64, lift +27.10.
- Predicted VOI: 0% review under primary capacities.
- Oracle VOI upper bound: +16.82 mean utility, lift +70.56.

Feature-separation repair:

- `funded_amnt` remains in the cash-flow outcome formula.
- `funded_amnt` is no longer in predictor groups.
- `feature_audit_loan_csv.csv` marks `funded_amnt` and repayment/recovery columns as `allowed_as_predictor=False`.

Claim boundary:

- This is accepted/funded-loan policy evaluation, not reject inference or full applicant-pool decisioning.
- Review is modeled as feature acquisition, not real human judgment.
- Cash prediction remains weak; policy utility comparison is the safe claim.
