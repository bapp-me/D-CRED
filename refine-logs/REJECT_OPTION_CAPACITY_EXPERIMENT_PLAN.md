# Reject-Option And Capacity-Aware D-CRED Experiment Plan

**Problem**: The current D-CRED thesis still looks like a patchwork around capped models, reused validation data, dangerous calibration-selection wording, and a weak conformal selective-decision layer. The new plan rebuilds the empirical story around a credit-specific reject-option decision rule with review capacity.

**Method Thesis**: A credible revised D-CRED should be a three-layer decision framework: calibrated probability-of-default modelling, cost-aware reject-option decisioning, and capacity-aware deferral. Split conformal becomes a baseline or risk-control variant, not the main decision rule.

**Date**: 2026-05-19

## Hard Reset Decisions

1. **No 50k training cap in final main tables**.
   - Full Lending Club training data must be used for every model in the final comparison.
   - If a model cannot run on the full training data, drop it from the main table or relabel it as an appendix engineering comparison.
   - Do not write "local stability" as a justification for truncating the primary evidence.

2. **No reused validation set for all downstream choices**.
   - Calibration fitting, calibration selection, threshold/policy tuning, conformal/risk-control calibration, and final testing must use separate chronological holdouts.

3. **No test-Brier selection**.
   - The chosen calibrated probability source must be selected before test evaluation.
   - Test results can report all calibrators, but the primary method must be pre-selected on the calibration-selection holdout.

4. **Replace the old selective-decision main claim**.
   - Old split conformal, uncertainty band, and all-review are comparison baselines.
   - The main method is the teacher-proposed credit-specific reject-option rule plus capacity-aware deferral.

## Frozen Data Protocol

Use Lending Club as the primary dataset. Build a new chronological split with six non-overlapping partitions:

| Partition | Purpose | Approx. Share | Allowed Uses |
|---|---:|---:|---|
| `model_train` | Fit PD models | 50% | Model fitting only |
| `model_dev` | Early stopping / model hyperparameter sanity | 10% | XGB/LightGBM early stopping and hyperparameter choice |
| `calibration_fit` | Fit Platt, isotonic, Venn-Abers | 10% | Calibration fitting only |
| `calibration_select` | Select calibrated probability source | 10% | Choose primary calibrator by validation Brier with ECE/NLL tie-break |
| `policy_tune` | Tune cost/reject-option scenario parameters | 10% | Select cost scenario grids and non-conformal policy variants |
| `risk_calibration` | Conformal / risk-control calibration | 5% | Split conformal and conformal risk control only |
| `final_test` | One-shot final report | 5% | Final evaluation only |

If the exact sample count makes 5% `final_test` too small, use a 45/10/10/10/10/5/10 split instead and keep `final_test` at 10%. The important rule is separation of roles, not the exact proportions. All split cut dates must be recorded in a CSV and in the dissertation.

Secondary datasets:

- UCI Default and German Credit are optional sanity checks only.
- They should not drive the main claim because they lack long temporal deployment structure.

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: Full-data calibrated PD models are reliable enough for downstream decisioning | Removes the 50k-cap and test-selection criticisms | Full-data LR/XGB/LightGBM-family models; calibrators fit and selected on non-test holdouts; final test Brier/ECE/NLL/reliability diagrams | B1 |
| C2: Credit-specific reject-option decisioning is the central D-CRED contribution | Replaces generic conformal sets with a decision rule grounded in credit costs | Cost-aware reject option beats no-review thresholding on cost-review trade-off under pre-registered cost assumptions | B2 |
| C3: Capacity-aware deferral solves the "91% review" weakness | Real review systems cannot review everything | Top-B deferral curves show cost reduction under fixed review budgets and expose the cost/capacity frontier | B3 |
| C4: Conformal methods are useful as risk-control baselines, not the sole decision layer | Keeps conformal evidence but prevents overclaiming | Standard split conformal, uncertainty band, and conformal risk-control variants compared against reject-option policies | B3, B4 |
| C5: Results are protocol-clean | Prevents defense failure on leakage/selection bias | Every selection step happens before final test; final test is evaluated once with a frozen config | B0 |

## Main Paper Storyline

Main paper must prove:

- Layer 1 gives calibrated PD estimates without test-set selection.
- Layer 2 converts calibrated PD into approve/deny/manual-review decisions using explicit expected costs.
- Layer 3 handles limited human review capacity and produces an interpretable cost-capacity frontier.

Appendix can support:

- All calibrator test metrics.
- Additional cost ratios and human-residual scenarios.
- UCI/German sanity checks.
- Old 50k-cap results as obsolete historical context, not final evidence.

Experiments intentionally cut:

- Fairness compliance.
- Reject-inference correction.
- Production-bank validation.
- Human-review empirical modelling without real reviewer labels.
- Strong top-venue novelty claims.

## Experiment Blocks

### Block 0: Protocol Rebuild And Test-Lock Gate

- **Claim tested**: The new experiment design removes the three protocol objections before any new result is trusted.
- **Why this block exists**: The teacher objections about 50k caps, validation reuse, and test-Brier selection are defense-critical.
- **Dataset / split / task**: Lending Club chronological split into role-specific partitions.
- **Compared systems**: Not applicable.
- **Metrics**:
  - Split row counts and date ranges.
  - Default rate per partition.
  - Feature availability audit.
  - Test-lock checklist.
- **Setup details**:
  - Generate `split_role_summary.csv`.
  - Generate `selection_protocol.md`.
  - Pre-register primary model families, calibrator-selection rule, cost scenarios, capacity grid, and final metrics before opening `final_test`.
  - Remove all final-table dependency on `tree_max_train_rows=50000`.
- **Success criterion**: A reviewer can trace every model/calibration/threshold/conformal decision to a non-test partition.
- **Failure interpretation**: If the pipeline cannot keep roles separate, the old MSc-ready claim is safer than the revised stronger claim.
- **Table / figure target**: Chapter 4 protocol table.
- **Priority**: MUST-RUN.

### Block 1: Layer 1 Full-Data Calibrated PD Model

- **Claim tested**: D-CRED has a credible calibrated PD layer trained on the full available training data.
- **Why this block exists**: The old RF/XGB cap and calibration-selection wording undermine the entire downstream decision layer.
- **Dataset / split / task**: Lending Club `model_train`, `model_dev`, `calibration_fit`, `calibration_select`, `final_test`.
- **Compared systems**:
  - Full-data scalable logistic model.
  - Full-data GPU XGBoost using RTX 4060, no training-row cap.
  - Full-data LightGBM-family model, no training-row cap.
  - Optional: actual full-data sklearn RandomForest only if it can run without row truncation; otherwise exclude from the main table.
- **Calibrators**:
  - Raw probability.
  - Platt/sigmoid.
  - Isotonic.
  - Venn-Abers probability interval.
- **Metrics**:
  - Primary: Brier, ECE, NLL.
  - Secondary: ROC-AUC, PR-AUC, reliability diagram.
  - Venn-Abers-specific: interval width, lower/upper interval summary, midpoint Brier/ECE/NLL, optional pessimistic decision sensitivity using interval bounds.
- **Setup details**:
  - Fit base models on `model_train`; use `model_dev` only for early stopping and model hyperparameter sanity.
  - Fit calibrators on `calibration_fit`.
  - Select the primary calibrated source on `calibration_select` by Brier, with ECE then NLL as tie-breakers.
  - Report final selected calibrator on `final_test` once.
  - Report all calibrators in appendix, clearly marked as post-hoc comparison, not selection.
- **Success criterion**: The final calibrated PD source is selected without test data and has acceptable Brier/ECE/NLL on `final_test`.
- **Failure interpretation**: If Venn-Abers does not beat isotonic as a point predictor, keep isotonic as primary and use Venn-Abers intervals for uncertainty-aware robustness only.
- **Table / figure target**: Main Layer 1 calibration table; reliability diagrams for selected calibrators.
- **Priority**: MUST-RUN.

### Block 2: Layer 2 Credit-Specific Cost-Aware Reject Option

- **Claim tested**: A credit-specific reject-option rule is a better decision layer than directly using conformal prediction sets for approve/reject/review.
- **Why this block exists**: This is the teacher's central recommendation and should become the revised method contribution.
- **Dataset / split / task**: Use the selected Layer 1 calibrated PD source. Tune only on `policy_tune`; evaluate on `final_test`.
- **Compared systems**:
  - No-review cost-sensitive threshold: choose approve/deny by `min(C_A, C_D)`.
  - All-review: every case goes to manual review under the same review-cost and residual-error assumptions.
  - Teacher-proposed reject option: choose `argmin {C_A, C_D, C_M}`.
  - Old uncertainty band baseline.
  - Old standard split conformal baseline.
- **Decision costs**:
  - `C_A(x) = c_FN * p(x)`.
  - `C_D(x) = c_FP * (1 - p(x))`.
  - `C_M(x) = c_R + C_human_residual(x)`.
  - Use `c_FP = 1`; test `c_FN:c_FP` ratios `{2:1, 5:1, 10:1}`.
  - Use review costs `c_R in {0.02, 0.05, 0.10, 0.20, 0.50}`.
  - Use human-residual stress values `rho in {0, 0.10, 0.25, 0.50}` with `C_human_residual(x) = rho * min(C_A(x), C_D(x))` unless a better reviewer model is implemented.
- **Metrics**:
  - Realized expected cost on final test.
  - Review rate.
  - Automation rate.
  - Approval/rejection rates.
  - Approved default rate.
  - Rejected good rate.
  - Savings versus no-review thresholding.
  - Savings versus all-review.
- **Setup details**:
  - The policy is deterministic once `p(x)`, cost ratios, review cost, and human-residual scenario are fixed.
  - Select one primary scenario before final test: likely `c_FN:c_FP=5:1`, `c_R=0.10`, `rho=0.10` or `rho=0.25`.
  - Put broader scenario grid in appendix.
- **Success criterion**: Reject option provides a non-trivial cost-review trade-off and avoids the old "review 91% by default" narrative.
- **Failure interpretation**: If all-review dominates under cheap perfect review, the paper must state that capacity constraints are necessary; the contribution shifts to Block 3.
- **Table / figure target**: Main Layer 2 decision table.
- **Priority**: MUST-RUN.

### Block 3: Layer 3 Cost-And-Capacity-Aware Deferral

- **Claim tested**: Review capacity turns reject-option decisioning into a realistic credit deployment policy.
- **Why this block exists**: Real lenders cannot send unlimited cases to review. This directly addresses the strongest weakness in old selective decisioning.
- **Dataset / split / task**: Use selected Layer 1 calibrated PD source and fixed cost scenarios. Tune capacity grid on `policy_tune`; evaluate on `final_test`.
- **Compared systems**:
  - No-review cost-sensitive threshold.
  - All-review.
  - Standard split conformal.
  - Uncertainty band.
  - Unlimited cost-aware reject option.
  - Capacity-aware deferral.
  - Conformal risk-control deferral variant.
- **Capacity rule**:
  - Compute automatic best cost: `C_auto(x) = min(C_A(x), C_D(x))`.
  - Compute manual-review cost: `C_M(x)`.
  - Compute review benefit: `Delta_i = C_auto(x_i) - C_M(x_i)`.
  - If review capacity is `B`, send only the top-`B` positive-Delta cases to review.
  - All remaining cases take the cheaper automatic action: approve if `C_A <= C_D`, deny otherwise.
- **Capacity grid**:
  - Fractions: `{1%, 2%, 5%, 10%, 20%, 30%, 50%}` of applications.
  - Optional absolute daily equivalent if the dissertation wants operational framing.
- **Metrics**:
  - Expected cost.
  - Review rate and capacity usage.
  - Approval/rejection/review shares.
  - Marginal cost saved per reviewed case.
  - Approved default rate.
  - Rejected good rate.
  - Cost-capacity frontier area or Pareto frontier.
- **Setup details**:
  - Report curves over capacity, not one cherry-picked point.
  - Main table should include the capacity that matches the old split-conformal review rate and smaller realistic budgets, e.g. 5%, 10%, 20%.
  - Top-B ranking uses only calibrated probability and cost assumptions, not labels.
- **Success criterion**: Capacity-aware deferral dominates uncertainty band and standard split conformal at practical review budgets, or at least clearly describes the trade-off frontier.
- **Failure interpretation**: If it does not dominate, the revised thesis can still claim that D-CRED exposes the true cost of review capacity rather than pretending conformal prediction solves deployment.
- **Table / figure target**: Main cost-vs-capacity curve; Pareto frontier table.
- **Priority**: MUST-RUN.

### Block 4: Conformal Risk-Control Variant

- **Claim tested**: Conformal methods can be integrated as a risk-control layer over the cost-aware deferral policy rather than replacing the decision rule.
- **Why this block exists**: It preserves the original conformal theme, but makes it subordinate to credit-specific costs.
- **Dataset / split / task**: Use `risk_calibration` to choose risk-control thresholds; evaluate on `final_test`.
- **Compared systems**:
  - Standard split conformal prediction-set review.
  - Capacity-aware deferral without conformal risk control.
  - Capacity-aware deferral with conformal risk-control threshold.
- **Risk-control targets**:
  - Bound average automated decision loss below a target.
  - Or bound approved-default rate among auto-approved loans below a target.
  - Or bound expected cost relative to no-review baseline.
- **Metrics**:
  - Test expected cost.
  - Empirical target violation.
  - Review rate / capacity usage.
  - Automation rate.
  - Coverage or risk-control diagnostic.
- **Setup details**:
  - Candidate thresholds are calibrated only on `risk_calibration`.
  - Final test is used only once.
  - If finite-sample guarantees are difficult to implement cleanly, label this as an empirical conformal risk-control variant and keep formal guarantees out of the thesis.
- **Success criterion**: The conformal variant offers a meaningful risk-control trade-off without exploding review rate to 91%.
- **Failure interpretation**: If review rate remains too high, standard conformal belongs in baseline/limitation discussion, not the main contribution.
- **Table / figure target**: Appendix or secondary main-table comparison.
- **Priority**: SHOULD-RUN.

### Block 5: Robustness And Ablation

- **Claim tested**: The revised contribution is not an artifact of one model, one cost ratio, or one reviewer-cost assumption.
- **Why this block exists**: Stronger supervisor scrutiny means the revised method needs robustness, but not a giant benchmark.
- **Dataset / split / task**: Lending Club final test; optional UCI/German sanity checks.
- **Compared systems**:
  - Selected PD model versus other full-data models.
  - Isotonic versus Venn-Abers midpoint and interval-pessimistic variants.
  - Reject option with and without capacity.
  - Capacity-aware deferral with different `rho` and `c_R`.
- **Metrics**:
  - Same cost/review/risk metrics as Blocks 2-3.
  - Robustness by scenario.
  - Seed mean/std for stochastic full-data XGB/LightGBM if feasible.
- **Setup details**:
  - Use 3 seeds for stochastic models if runtime permits.
  - Do not use reduced UCI/German as proof of temporal deployment; keep them as sanity checks.
- **Success criterion**: Main qualitative conclusion remains stable across primary cost scenarios and at least two full-data PD models.
- **Failure interpretation**: If results depend heavily on one PD model or one cost ratio, narrow the claim to a case study.
- **Table / figure target**: Appendix robustness matrix; one concise main-text robustness paragraph.
- **Priority**: SHOULD-RUN.

## Run Order And Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 | Rebuild split protocol and freeze test | R001-R004 | All downstream choices have a non-test source | 0.5 day CPU | Split sizes may need adjustment to keep final test large enough |
| M1 | Train full-data PD models | R101-R104 | At least two full-data models complete without row caps | 0.5-3 days, RTX 4060 for XGB | sklearn RF may still fail; drop or move to appendix instead of capping |
| M2 | Fit and select calibrators without test | R201-R204 | Primary calibrated source selected on `calibration_select` | 0.5-1 day CPU | Venn-Abers may be weaker as midpoint; use interval value if so |
| M3 | Implement reject-option policies | R301-R305 | Cost-aware reject option beats or clarifies no-review/all-review trade-off | 0.5-1 day CPU | All-review may dominate when review is cheap and perfect |
| M4 | Implement capacity-aware deferral | R401-R405 | Cost-capacity frontier is generated and compared to baselines | 0.5-1 day CPU | Practical capacities may reduce savings; report honestly |
| M5 | Add conformal risk-control variant | R501-R504 | Conformal variant has a clear risk-control role or is demoted | 1-2 days CPU/GPU optional | Formal guarantee may be hard to present cleanly |
| M6 | Final locked test report and claim audit | R601-R604 | One final test report maps directly to thesis claims | 0.5-1 day | Any post-test method change requires a new frozen run label |

## Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | Create chronological role split | Data protocol | Lending full | dates, rows, default rate | MUST | TODO | No model training |
| R002 | M0 | Write selection protocol | Protocol doc | All partitions | checklist | MUST | TODO | Pre-register calibrator, policy, capacity grid |
| R003 | M0 | Remove capped-result dependency | Claim audit | Existing thesis/results | table-source audit | MUST | TODO | Old 50k-cap rows move out of main evidence |
| R004 | M0 | Validate no test access before final | Pipeline guard | `final_test` | access log | MUST | TODO | Final test should only be loaded by final report step |
| R101 | M1 | Full-data LR baseline | SGD/logistic | model_train/model_dev | AUC, Brier raw | MUST | TODO | No train-row cap |
| R102 | M1 | Full-data GPU XGB | XGBoost CUDA | model_train/model_dev | AUC, Brier raw | MUST | TODO | Use RTX 4060, no train-row cap |
| R103 | M1 | Full-data LightGBM-family baseline | LightGBM GBDT/RF | model_train/model_dev | AUC, Brier raw | MUST | TODO | No train-row cap; label precisely |
| R104 | M1 | Optional actual full RF | sklearn RF or alternative | model_train/model_dev | AUC, Brier raw | NICE | TODO | Drop if full run fails; do not cap |
| R201 | M2 | Fit Platt/isotonic | Calibration | calibration_fit | calibration objects | MUST | TODO | No test metrics |
| R202 | M2 | Fit Venn-Abers interval | Calibration | calibration_fit | interval width | MUST | TODO | Report midpoint and interval metrics |
| R203 | M2 | Select primary calibrated source | Selection | calibration_select | Brier, ECE, NLL | MUST | TODO | This replaces all test-Brier wording |
| R204 | M2 | Produce Layer 1 final report | Locked evaluation | final_test | Brier, ECE, NLL, reliability | MUST | TODO | One-shot final report |
| R301 | M3 | Implement no-review threshold baseline | Decision | policy_tune/final_test | cost, approvals | MUST | TODO | `min(C_A,C_D)` |
| R302 | M3 | Implement all-review reference | Decision | policy_tune/final_test | cost, review rate | MUST | TODO | Uses same `c_R` and `rho` scenarios |
| R303 | M3 | Implement cost-aware reject option | Decision | policy_tune/final_test | cost, review, automation | MUST | TODO | `argmin {C_A,C_D,C_M}` |
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
| R604 | M6 | Hard reviewer pass | Review | all outputs | MSc defensibility | SHOULD | TODO | Use `msc-thesis-critical-review` after results |

## Compute And Data Budget

- **GPU**: Use local RTX 4060 for full-data XGBoost and any expensive repeated runs.
- **Expected GPU time**: 12-72 GPU-hours depending on full-data XGB seeds and hyperparameter grid.
- **CPU time**: 1-3 days for LightGBM, calibration, Venn-Abers, policy grids, and reporting.
- **Storage**: Save prediction parquet/CSV for each partition and model; this is necessary to avoid retraining for policy experiments.
- **Key artifact requirement**: Store out-of-sample calibrated probabilities for every holdout partition, with a provenance column indicating model, calibrator, partition, seed, and selection status.

## Implementation Notes

- The final paper should not call the capped old LightGBM RF result "RF" in the main model table.
- If full-data LightGBM RF is kept, call it "LightGBM-RF full-data" and record that it uses all training rows.
- If actual sklearn RandomForest cannot finish on the full dataset, exclude it from the main comparison. This is methodologically cleaner than capping at 50k.
- Venn-Abers can be used in two ways:
  - midpoint probability for Brier/ECE/NLL comparison;
  - interval bounds for pessimistic cost decisions, e.g. approve cost using upper PD bound.
- The primary result should be a cost-capacity curve, not a single cherry-picked review rate.
- If all-review dominates under perfect cheap review, state that real deployment requires capacity constraints and residual human error; do not hide this.

## Risks And Mitigations

- **Risk**: Full-data XGB or LightGBM is slow on the laptop.
  - **Mitigation**: Runtime is allowed; use checkpointed prediction outputs and one model at a time. Do not reintroduce row caps.
- **Risk**: Full-data sklearn RandomForest fails again.
  - **Mitigation**: Drop it from the main table. The thesis does not need sklearn RF if full-data XGB/LightGBM/logistic are credible.
- **Risk**: Venn-Abers does not improve point calibration.
  - **Mitigation**: Keep isotonic as selected PD source; use Venn-Abers interval as uncertainty/robustness evidence.
- **Risk**: Cost-aware reject option reviews too many cases.
  - **Mitigation**: Capacity-aware deferral is the main Layer 3 result; unlimited reject option is an intermediate.
- **Risk**: Capacity-aware deferral only wins under unrealistic human-review assumptions.
  - **Mitigation**: Present residual-error sensitivity and narrow claims to "decision analysis under stated assumptions."
- **Risk**: Conformal risk-control variant is weak or complicated.
  - **Mitigation**: Keep it as a baseline/appendix result. Do not make formal conformal guarantees unless implementation is clean.

## Final Checklist

- [ ] Final model table uses full training data, no 50k cap.
- [ ] Calibration fitting, selection, policy tuning, risk calibration, and final test use separate partitions.
- [ ] Primary calibrated source is selected before final test.
- [ ] Test Brier appears only as final reporting, not selection.
- [ ] Layer 1 reports Brier, ECE, NLL, and reliability diagrams.
- [ ] Layer 2 implements `argmin {C_A, C_D, C_M}`.
- [ ] Layer 3 implements top-B capacity-aware deferral using positive `Delta_i`.
- [ ] Baselines include no-review threshold, all-review, split conformal, uncertainty band, reject option, capacity-aware deferral, and conformal risk-control variant.
- [ ] Main claim is about cost-review-capacity trade-offs, not production-bank deployment.
- [ ] `CLAIMS_FROM_RESULTS.md` is rewritten after the new final report.

