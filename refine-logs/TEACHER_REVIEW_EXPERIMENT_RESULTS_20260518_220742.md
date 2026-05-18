# Teacher Review P0/P1 Experiment Results

Date: 2026-05-18 22:08:07
Plan: `refine-logs/TEACHER_REVIEW_EXPERIMENT_PLAN.md`
Source results: `outputs/review_round1_fix/`
Run output: `outputs\teacher_review_p1_20260518_220742`

## Results By Milestone

### M0: P0 Protocol And Claim-Control Gate - DONE

| run_id   | check                                                                   | status   | note                                                                                     |
|:---------|:------------------------------------------------------------------------|:---------|:-----------------------------------------------------------------------------------------|
| R001     | Calibration selection is validation-based; test Brier is reporting only | PASS     | Code fits/chooses calibrators on validation records and reports test metrics separately. |
| R002     | Validation reuse limitation is explicit                                 | PASS     | The limitation should cover calibration, threshold selection, and conformal quantiles.   |
| R002     | 50k tree cap and LightGBM-RF surrogate are explicit                     | PASS     | Required for conservative model-comparison claims.                                       |
| R002     | Reviewed cases are cost-only with no residual manual-review error       | PASS     | This is the assumption stressed by the new sensitivity analysis.                         |
| R003     | No unsupported high-automation wording                                  | PASS     | The evidence supports review-heavy risk control, not high automation.                    |
| R003     | No production-bank or fairness-compliance claim                         | PASS     | These should appear only as limitations/future work.                                     |
| R003     | Temporal AUC is not claimed uniformly worse                             | PASS     | C1 should remain a deployment-setting claim.                                             |

### M1: Temporal Drift Attribution - DONE

| comparison          |   train_default_rate |   comparison_default_rate |   default_rate_delta | top_psi_feature   |   top_psi | top_psi_type   | top_ks_feature   |   top_ks_statistic | interpretation         |
|:--------------------|---------------------:|--------------------------:|---------------------:|:------------------|----------:|:---------------|:-----------------|-------------------:|:-----------------------|
| validation_vs_train |             0.183791 |                  0.229628 |            0.0458368 | zip_code          | 0.03941   | categorical    | revenue          |          0.0445877 | mainly base-rate shift |
| test_vs_train       |             0.183791 |                  0.217933 |            0.0341418 | purpose           | 0.0614623 | categorical    | revenue          |          0.087352  | mainly base-rate shift |

### M2: Selective Decisioning Sensitivity - DONE

| model   |   coverage |   automation_rate |   review_rate |   approval_rate |   rejection_rate |   approved_default_rate |   expected_cost |
|:--------|-----------:|------------------:|--------------:|----------------:|-----------------:|------------------------:|----------------:|
| lr      |   0.898433 |         0.0934417 |      0.906558 |       0.0934417 |      0           |               0.0646788 |        0.120874 |
| rf      |   0.900641 |         0.0779151 |      0.922085 |       0.0779151 |      0           |               0.061378  |        0.11612  |
| xgb     |   0.897435 |         0.0903512 |      0.909649 |       0.0903216 |      2.96805e-05 |               0.0602588 |        0.118197 |

### M3: Manual-Review Residual-Error Sensitivity

The stress test adds residual classification-error cost on reviewed cases; it is a scenario analysis, not measured reviewer performance.

| model   |   manual_residual_error_rate |   expected_cost |   delta_vs_robust_cost |   delta_vs_cost_5_to_1 |   automation_rate |   review_rate |
|:--------|-----------------------------:|----------------:|-----------------------:|-----------------------:|------------------:|--------------:|
| lr      |                         0    |        0.120874 |              -0.604013 |              -0.543673 |         0.0934417 |      0.906558 |
| lr      |                         0.01 |        0.138415 |              -0.586472 |              -0.526132 |         0.0934417 |      0.906558 |
| lr      |                         0.03 |        0.173498 |              -0.55139  |              -0.491049 |         0.0934417 |      0.906558 |
| lr      |                         0.05 |        0.20858  |              -0.516307 |              -0.455967 |         0.0934417 |      0.906558 |
| lr      |                         0.1  |        0.296286 |              -0.428602 |              -0.368261 |         0.0934417 |      0.906558 |
| rf      |                         0    |        0.11612  |              -0.616726 |              -0.560552 |         0.0779151 |      0.922085 |
| rf      |                         0.01 |        0.133867 |              -0.598979 |              -0.542805 |         0.0779151 |      0.922085 |
| rf      |                         0.03 |        0.16936  |              -0.563485 |              -0.507311 |         0.0779151 |      0.922085 |
| rf      |                         0.05 |        0.204854 |              -0.527991 |              -0.471817 |         0.0779151 |      0.922085 |
| rf      |                         0.1  |        0.293589 |              -0.439257 |              -0.383083 |         0.0779151 |      0.922085 |
| xgb     |                         0    |        0.118197 |              -0.606205 |              -0.547415 |         0.0903512 |      0.909649 |
| xgb     |                         0.01 |        0.135792 |              -0.588609 |              -0.529819 |         0.0903512 |      0.909649 |
| xgb     |                         0.03 |        0.170984 |              -0.553418 |              -0.494628 |         0.0903512 |      0.909649 |
| xgb     |                         0.05 |        0.206175 |              -0.518226 |              -0.459437 |         0.0903512 |      0.909649 |
| xgb     |                         0.1  |        0.294153 |              -0.430248 |              -0.371458 |         0.0903512 |      0.909649 |

Break-even residual-error rates:

| model   | baseline    |   break_even_manual_residual_error_rate | interpretation                                   |
|:--------|:------------|----------------------------------------:|:-------------------------------------------------|
| lr      | robust_cost |                                0.344341 | benefit survives the tested residual-error range |
| lr      | cost_5_to_1 |                                0.309941 | benefit survives the tested residual-error range |
| rf      | robust_cost |                                0.347512 | benefit survives the tested residual-error range |
| rf      | cost_5_to_1 |                                0.315859 | benefit survives the tested residual-error range |
| xgb     | robust_cost |                                0.34452  | benefit survives the tested residual-error range |
| xgb     | cost_5_to_1 |                                0.311108 | benefit survives the tested residual-error range |

### M4: Cost And Profit Scenario Consolidation - DONE

| model   | policy      |   expected_cost |   delta_vs_fixed_0.5 |   approval_rate |   approved_default_rate |
|:--------|:------------|----------------:|---------------------:|----------------:|------------------------:|
| lr      | cost_5_to_1 |        0.664547 |            -0.401073 |        0.352345 |                0.111077 |
| rf      | cost_5_to_1 |        0.676671 |            -0.403062 |        0.33795  |                0.114689 |
| xgb     | cost_5_to_1 |        0.665612 |            -0.409691 |        0.37058  |                0.114291 |

## Claim Interpretation

- C1 is strengthened as a bounded deployment-setting claim: the temporal validation/test periods have higher default rates than train, and the PSI/KS table identifies which application-time features moved most.
- C3 remains the strongest quantitative claim: cost-aware thresholds reduce expected cost versus fixed 0.5 under the stated FN:FP scenarios.
- C4 remains conservative: split conformal is review-heavy and should be described as risk-control analysis, not high-automation lending.
- Manual-review residual-error rows should be used as a limitation/stress test; they do not estimate real human reviewer quality.

## Output Files

- `temporal_drift_summary.csv`
- `temporal_feature_shift_psi_ks.csv`
- `selective_alpha_review_cost_tradeoff.csv`
- `selective_reference_policies.csv`
- `selective_reviewed_cohort_profile.csv`
- `manual_review_residual_error_sensitivity.csv`
- `manual_review_break_even_error.csv`
- `cost_policy_scenario_summary.csv`
- `profit_policy_scenario_summary.csv`
- `number_source_map.csv`
