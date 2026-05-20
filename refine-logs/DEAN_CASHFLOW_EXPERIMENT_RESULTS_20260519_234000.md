# Dean Cash-Flow Experiment Results

Date: 2026-05-19

Primary run:

- `outputs/dean_cashflow_full/`
- implementation: `scripts/cashflow_feature_acquisition_experiment.py`
- raw data: `data/raw/lending_club/loan.csv`

## Executive Conclusion

The dean's four proposed experiment directions are implementable on the downloaded Lending Club `loan.csv`, and all four were run on the full terminal accepted-loan sample.

The strongest dissertation update is not "predicted VOI wins". The strongest update is:

> Observed loan-level cash flow materially changes the decision objective; under a strict month-blocked final test, a tuned cash-flow decision policy dominates fixed and tuned PD thresholds, while a conformal-style budgeted review frontier produces the best non-oracle acquisition result.

The predicted value-of-information learner selected zero reviews under the primary final-test setting. That is a negative result and should be preserved, not hidden.

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

Cash-flow fields are present and used only as outcome labels. They are not predictors.

## Experiment 1: Economic Utility Decisioning

Final-test mean realized utility per application:

| Policy | Mean utility | Approval rate | Interpretation |
|---|---:|---:|---|
| Fixed PD threshold 0.5 | -518.09 | 65.17% | Bad under 2017-2018 cash-flow drift. |
| Tuned PD threshold | -109.06 | 30.10% | Much better than fixed threshold. |
| Direct cash model, threshold 0 | -1670.24 | 99.96% | Fails because predicted positive cash approves almost all loans. |
| Tuned cash model | -24.07 | 0.71% | Best direct policy, but very conservative and has high missed-profitable-loan opportunity cost. |

Conclusion:

- The observed cash-flow objective is materially different from binary default-threshold evaluation.
- A tuned cash-flow policy is stronger than tuned PD on final-test realized utility.
- The result is conservative and drift-sensitive: the best policy approves very few loans, so the thesis must discuss opportunity cost.

## Experiment 2: Feature Acquisition

Final-test model quality:

| Scope | PD AUC | PD Brier | Cash MAE |
|---|---:|---:|---:|
| Cheap features | 0.6465 | 0.2362 | 4076.8 |
| Full review features | 0.6772 | 0.2137 | 3786.1 |

Conclusion:

- Acquired review features improve both PD and cash prediction on final test.
- The gain is real but moderate; this supports an information-acquisition framing, not a claim that review magically fixes all errors.
- Some numeric full-feature fields are all missing in the training split and are skipped by sklearn; this is a feature-availability limitation, not a cash-flow-field limitation.

## Experiment 3: Capacity Frontier

Primary review cost: $10 per reviewed loan.

Key final-test frontier rows:

| Policy | Capacity | Review rate | Mean utility | Lift vs no review | ROI per review dollar |
|---|---:|---:|---:|---:|---:|
| No-review cheap model | n/a | 0.00% | -48.51 | n/a | n/a |
| All-review full model | n/a | 100.00% | -34.07 | +14.44 | +1.44 |
| Conformal interval review | 5% | 5.00% | -21.56 | +26.95 | +53.91 |
| Conformal interval review | 10% | 10.00% | -24.02 | +24.49 | +24.49 |
| Conformal interval review | 20% | 20.00% | -26.07 | +22.44 | +11.22 |
| D-CRED stylized benefit rank | 5% | 5.00% | -48.08 | +0.43 | +0.86 |
| Predicted VOI | 5%-50% | 0.00% | -48.51 | 0.00 | n/a |
| Oracle VOI upper bound | 5%-50% | 0.49% | +17.31 | +65.82 | +1353.79 |

Conclusion:

- The strongest non-oracle acquisition policy is conformal interval review around the tuned cash-decision boundary.
- Predicted VOI fails in this run by selecting zero reviews after cost filtering. This is a useful boundary condition.
- The oracle gap is large, so the dissertation can claim that the problem has exploitable review value, but the learned VOI scorer is not yet the winning mechanism.

## Experiment 4: Cost And Robustness Sensitivity

Review-cost grid:

- Conformal interval review remains positive across direct review costs $5-$100.
- At 10% review capacity, lift declines from +24.99 per application at $5 to +15.49 at $100.
- At 20% review capacity and $100 review cost, lift is still positive but small: +4.44 per application, ROI +0.22 per review dollar.

Loss/profit ratio stress at 10% review capacity:

| Loss/profit ratio | Conformal lift vs no review |
|---:|---:|
| 1.0 | -7.65 |
| 2.0 | -5.75 |
| 5.0 | -0.03 |
| 10.0 | +9.51 |
| 11.4 | +12.18 |
| 15.0 | +19.04 |
| 20.0 | +28.58 |

Conclusion:

- The conformal review rule is most defensible when downside losses are materially larger than upside gains.
- This directly supports a cost-aware credit-risk narrative, but not a universal "review always helps" claim.

## What Was Not Run

Not run, by design:

- Rejected-applicant inference: `loan.csv` is an accepted/funded-loan book, so this is funded-loan policy evaluation.
- Real human reviewer accuracy: review is modeled as acquisition of additional observed features, not human judgment.
- Causal deployment ROI: no randomized lending-policy intervention exists here.
- FICO-specific experiments: this `loan.csv` header does not expose FICO fields, although it does include many credit-history and utilization fields.

## Writing Guidance

Use these claims:

- "Observed Lending Club repayment fields allow D-CRED to evaluate loan-level net cash, not only binary default cost."
- "A tuned cash-flow policy improves final-test utility relative to fixed and tuned PD thresholds, but does so with a very low approval rate."
- "Full review features improve prediction quality; the strongest budgeted-review rule in this run is conformal interval review near the tuned decision boundary."
- "Predicted VOI is a negative result in the current run; it should be reported as such."

Do not claim:

- universal profitability,
- real rejected-applicant fairness or reject inference,
- real human reviewer superiority,
- FICO-specific evidence,
- predicted VOI as the winning method.
