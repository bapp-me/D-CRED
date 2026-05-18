# Reject-Option And Capacity-Aware Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | Create chronological role split | Data protocol | Lending full | dates, rows, default rate | MUST | TODO | No model training |
| R002 | M0 | Write selection protocol | Protocol doc | All partitions | checklist | MUST | TODO | Pre-register calibrator, policy, capacity grid |
| R003 | M0 | Remove capped-result dependency | Claim audit | Existing thesis/results | table-source audit | MUST | TODO | Old 50k-cap rows move out of main evidence |
| R004 | M0 | Validate no test access before final | Pipeline guard | final_test | access log | MUST | TODO | Final test should only be loaded by final report step |
| R101 | M1 | Full-data LR baseline | SGD/logistic | model_train/model_dev | AUC, Brier raw | MUST | TODO | No train-row cap |
| R102 | M1 | Full-data GPU XGB | XGBoost CUDA | model_train/model_dev | AUC, Brier raw | MUST | TODO | Use RTX 4060, no train-row cap |
| R103 | M1 | Full-data LightGBM-family baseline | LightGBM GBDT/RF | model_train/model_dev | AUC, Brier raw | MUST | TODO | No train-row cap; label precisely |
| R104 | M1 | Optional actual full RF | sklearn RF or alternative | model_train/model_dev | AUC, Brier raw | NICE | TODO | Drop if full run fails; do not cap |
| R201 | M2 | Fit Platt/isotonic | Calibration | calibration_fit | calibration objects | MUST | TODO | No test metrics |
| R202 | M2 | Fit Venn-Abers interval | Calibration | calibration_fit | interval width | MUST | TODO | Report midpoint and interval metrics |
| R203 | M2 | Select primary calibrated source | Selection | calibration_select | Brier, ECE, NLL | MUST | TODO | This replaces all test-Brier wording |
| R204 | M2 | Produce Layer 1 final report | Locked evaluation | final_test | Brier, ECE, NLL, reliability | MUST | TODO | One-shot final report |
| R301 | M3 | Implement no-review threshold baseline | Decision | policy_tune/final_test | cost, approvals | MUST | TODO | min(C_A,C_D) |
| R302 | M3 | Implement all-review reference | Decision | policy_tune/final_test | cost, review rate | MUST | TODO | Uses same c_R and rho scenarios |
| R303 | M3 | Implement cost-aware reject option | Decision | policy_tune/final_test | cost, review, automation | MUST | TODO | argmin {C_A,C_D,C_M} |
| R304 | M3 | Compare old uncertainty/conformal baselines | Baselines | risk_calibration/final_test | cost, review, coverage | MUST | TODO | Old methods become baselines |
| R305 | M3 | Scenario grid for costs and residual error | Stress test | final_test | cost frontier | SHOULD | TODO | Main scenario plus appendix grid |
| R401 | M4 | Compute Delta ranking | Capacity deferral | final_test | Delta, positive benefit | MUST | TODO | No labels in ranking |
| R402 | M4 | Run capacity grid | Top-B deferral | final_test | cost vs review budget | MUST | TODO | 1%, 2%, 5%, 10%, 20%, 30%, 50% |
| R403 | M4 | Compare capacity-aware policy to baselines | Policy comparison | final_test | cost, review, approvals | MUST | TODO | Main revised result |
| R404 | M4 | Pareto frontier table | Analysis | final_test | Pareto dominance | MUST | TODO | Main paper figure |
| R405 | M4 | Cohort diagnosis for deferred cases | Diagnostics | final_test | feature profile, default rate | SHOULD | TODO | Shows which cases consume capacity |
| R501 | M5 | Calibrate conformal risk-control threshold | CRC variant | risk_calibration | target risk | SHOULD | TODO | Separate from policy tune |
| R502 | M5 | Evaluate CRC deferral | CRC variant | final_test | violation, cost, review | SHOULD | TODO | Compare against capacity-aware deferral |
| R503 | M5 | Standard split-conformal baseline | Baseline | risk_calibration/final_test | coverage, cost, review | MUST | TODO | Baseline only |
| R504 | M5 | Decide conformal claim status | Claim audit | results | supported/unsupported | MUST | TODO | Main method only if useful |
| R601 | M6 | Generate final tables and figures | Reporting | final_test | all locked metrics | MUST | TODO | No post-test method changes |
| R602 | M6 | Update CLAIMS_FROM_RESULTS | Claim control | final report | claim map | MUST | TODO | Old claims replaced |
| R603 | M6 | Update dissertation method/results plan | Writing handoff | thesis | section map | MUST | TODO | New Layer 1/2/3 structure |
| R604 | M6 | Hard reviewer pass | Review | all outputs | MSc defensibility | SHOULD | TODO | Use msc-thesis-critical-review after results |

