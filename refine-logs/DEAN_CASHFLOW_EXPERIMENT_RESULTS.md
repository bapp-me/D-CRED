# Dean Cash-Flow Experiment Results

Date: 2026-05-20

Primary run:

- `outputs/dean_cashflow_full/`
- implementation: `scripts/cashflow_feature_acquisition_experiment.py`
- raw data: `data/raw/lending_club/loan.csv`
- repair: removed `funded_amnt` from predictor groups after the nightmare reviewer found it was both a cash-flow component and a cheap predictor.

## Executive Conclusion

The dean's four proposed experiment directions are implementable on the downloaded Lending Club `loan.csv`, and all four were rerun on the full terminal accepted-loan sample after fixing the `funded_amnt` feature-separation issue.

The strongest dissertation update remains:

> Observed loan-level cash flow materially changes the decision objective; under a strict month-blocked final test, a tuned cash-flow decision policy beats fixed and tuned PD thresholds, while a conformal-style budgeted review frontier produces the best non-oracle acquisition result.

This is still not a "predicted VOI wins" result. The predicted value-of-information learner selected zero reviews under the primary final-test setting, and that negative result should be preserved.

## Data And Split

- Raw file: `data/raw/lending_club/loan.csv`
- Terminal accepted-loan rows: 1,306,387
- Good terminal rows: 1,043,940
- Bad terminal rows: 262,447
- Final-test rows: 67,461
- Final-test period: 2017-11 through 2018-12
- Split protocol: month-blocked seven-role split; no issue month is shared across roles.

Cash outcome:

```text
net_cash =
  total_rec_prncp
  + total_rec_int
  + total_rec_late_fee
  + recoveries
  - funded_amnt
  - collection_recovery_fee
```

Cash-flow fields are present and used only as outcome labels. They are not predictors. `feature_audit_loan_csv.csv` now marks `funded_amnt`, repayment, recovery, and collection-fee fields as `allowed_as_predictor=False`; `loan_amnt` remains the application-time amount feature.

## Experiment 1: Economic Utility Decisioning

Final-test mean realized utility per application:

| Policy | Mean utility | Approval rate | Interpretation |
|---|---:|---:|---|
| Fixed PD threshold 0.5 | -524.14 | 65.35% | Bad under 2017-2018 cash-flow drift. |
| Tuned PD threshold | -109.12 | 29.86% | Much better than fixed threshold. |
| Direct cash model, threshold 0 | -1670.00 | 99.91% | Fails because predicted positive cash approves almost all loans. |
| Tuned cash model | -25.96 | 0.74% | Best direct policy, but very conservative and has high missed-profitable-loan opportunity cost. |

Conclusion:

- The observed cash-flow objective is materially different from binary default-threshold evaluation.
- A tuned cash-flow policy is stronger than tuned PD on final-test realized utility even after removing `funded_amnt` from predictors.
- The result is conservative and drift-sensitive: the best policy approves very few loans, so the thesis must discuss opportunity cost.

## Experiment 2: Feature Acquisition

Final-test model quality:

| Scope | PD AUC | PD Brier | Cash MAE | Cash R2 |
|---|---:|---:|---:|---:|
| Cheap features | 0.6460 | 0.2358 | 4067.2 | -0.5663 |
| Full review features | 0.6768 | 0.2132 | 3795.6 | -0.4867 |

Conclusion:

- Acquired review features improve both PD and cash prediction on final test.
- The gain is real but moderate; this supports an information-acquisition framing, not a claim that review magically fixes all errors.
- Cash regression remains weak under temporal drift, so the paper should emphasize realized policy utility and claim boundaries rather than accurate profit prediction.
- Some numeric full-feature fields are all missing in the training split and are skipped by sklearn; this is a feature-availability limitation, not a cash-flow-field limitation.

## Experiment 3: Capacity Frontier

Primary review cost: $10 per reviewed loan.

Key final-test frontier rows:

| Policy | Capacity | Review rate | Mean utility | Lift vs no review | ROI per review dollar |
|---|---:|---:|---:|---:|---:|
| No-review cheap model | n/a | 0.00% | -53.74 | n/a | n/a |
| All-review full model | n/a | 100.00% | -35.96 | +17.77 | +1.78 |
| Conformal interval review | 5% | 5.00% | -25.16 | +28.57 | +57.15 |
| Conformal interval review | 10% | 10.00% | -26.64 | +27.10 | +27.10 |
| Conformal interval review | 20% | 20.00% | -27.96 | +25.77 | +12.89 |
| Conformal interval review | 50% | 50.00% | -30.96 | +22.77 | +4.55 |
| D-CRED stylized benefit rank | 5% | 5.00% | -53.67 | +0.06 | +0.13 |
| Predicted VOI | 5%-50% | 0.00% | -53.74 | 0.00 | n/a |
| Oracle VOI upper bound | 5%-50% | 0.51% | +16.82 | +70.56 | +1395.83 |

Conclusion:

- The strongest non-oracle acquisition policy is conformal interval review around the tuned cash-decision boundary.
- Predicted VOI fails in this run by selecting zero reviews after cost filtering. This is a useful negative result and should not be hidden.
- The oracle gap is large, so the dissertation can claim that review value exists in principle, but the learned VOI scorer is not yet the winning mechanism.

## Experiment 4: Cost And Robustness Sensitivity

Review-cost grid:

- At 5%, 10%, and 20% review capacity, conformal interval review remains positive across direct review costs $5-$100.
- At $100 review cost, lift declines as capacity rises: +24.07 at 5%, +18.10 at 10%, +7.77 at 20%, but turns negative at 30% (-2.23) and 50% (-22.23).
- Therefore the defensible claim is not "review always helps"; it is "review helps when review capacity and cost are in a favorable regime."

Loss/profit ratio stress at 10% review capacity:

| Loss/profit ratio | Conformal lift vs no review |
|---:|---:|
| 1.0 | -7.71 |
| 2.0 | -5.64 |
| 5.0 | +0.55 |
| 10.0 | +10.88 |
| 11.4 | +13.77 |
| 15.0 | +21.20 |
| 20.0 | +31.52 |

Conclusion:

- The conformal review rule is most defensible when downside losses are materially larger than upside gains.
- This supports a cost-aware credit-risk narrative, but not a universal "review always helps" claim.

## What Was Not Run

Not run, by design:

- Rejected-applicant inference: `loan.csv` is an accepted/funded-loan book, so this is funded-loan policy evaluation.
- Real human reviewer accuracy: review is modeled as acquisition of additional observed features, not human judgment.
- Causal deployment ROI: no randomized lending-policy intervention exists here.
- FICO-specific experiments: this `loan.csv` header does not expose FICO fields, although it includes many credit-history and utilization fields.

## Writing Guidance

Use these claims:

- "Observed Lending Club repayment fields allow D-CRED to evaluate loan-level net cash, not only binary default cost."
- "A tuned cash-flow policy improves final-test utility relative to fixed and tuned PD thresholds, but does so with a very low approval rate."
- "Full review features improve prediction quality; the strongest budgeted-review rule in this run is conformal interval review near the tuned decision boundary."
- "Predicted VOI is a negative result in the current run; it should be reported as such."
- "The clean rerun excludes cash-flow/post-origination columns, including `funded_amnt`, from predictors."

Do not claim:

- universal profitability,
- real rejected-applicant fairness or reject inference,
- real human reviewer superiority,
- FICO-specific evidence,
- predicted VOI as the winning method,
- accurate expected net-cash prediction,
- review benefit across the full cost-capacity grid.
