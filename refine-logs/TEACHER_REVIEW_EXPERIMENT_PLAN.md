# Teacher Review P0/P1 Experiment Plan

**Problem**: Convert the two supervisor reviews into a minimal, claim-driven reinforcement plan for the D-CRED MSc dissertation.

**Method Thesis**: D-CRED should remain a deployment-oriented credit-risk evaluation and decisioning framework; the extra work should strengthen protocol credibility, temporal-shift interpretation, and conservative selective-decision analysis without expanding into a new production banking system.

**Date**: 2026-05-18

## Scope Decision

This plan covers only P0 and P1 items from the supervisor-review prioritisation.

- **P0**: must be fixed before submission, mostly through writing, protocol clarification, and claim control.
- **P1**: should be added if time allows before final dissertation writing; these are compact analyses that improve examiner confidence without changing the main D-CRED method.
- **Excluded**: rolling-window OOT validation, full fairness compliance, reject inference, production-bank validation, full SHAP study, and complete instance-dependent financial modelling. These are P2/P3 for the MSc target.

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: Temporal evaluation changes the deployment setting | Defends the time-aware part of D-CRED without falsely claiming random splits overstate AUC | Show temporal split differs in default rate and selected feature distributions; do not claim temporal AUC is worse | B0, B1 |
| C2: Calibration matters for probability quality | Defends probability-focused decisioning rather than pure ranking metrics | Clarify calibrators are fitted and selected on validation, not test; report Brier/ECE improvements as probability-quality evidence | B0 |
| C3: Cost-aware thresholding is useful under stated assumptions | Main quantitative result; strongest current evidence | Retain paired cost deltas, add cost/profit scenario summary, avoid claiming real-bank value is fully proven | B0, B4 |
| C4: Selective decisioning is conservative risk control | Prevents overclaiming the weak 91% review result | Show alpha/review-cost sensitivity, automation-review-cost trade-off, reviewed cohort profile, and residual manual-review-error sensitivity | B0, B2, B3 |
| C5: Current evidence is MSc-level, not top-venue or production-level | Protects dissertation credibility | Explicit limitation block: validation reuse, 50k tree cap, LightGBM-RF surrogate, 3-seed reduced datasets, no fairness/reject-inference/production claim | B0 |

## Paper Storyline

Main paper must prove:

- D-CRED is a coherent framework for leakage-aware, time-aware, calibrated, cost-sensitive credit-risk decision evaluation.
- The strongest empirical contribution is calibration plus cost-aware thresholding.
- Selective conformal decisioning should be interpreted as a conservative, review-heavy risk-control layer.

Appendix can support:

- PSI/KS feature-shift tables.
- Selective alpha/review-cost sensitivity tables.
- Manual-review residual-error sensitivity.
- Cost/profit scenario tables.

Experiments intentionally cut:

- Rolling-window OOT cross-validation.
- Full fairness compliance or legally framed subgroup fairness claims.
- SHAP-based model explanation.
- Full dynamic instance-level loan profit/loss redesign.
- New datasets or production-bank validation.

## Experiment Blocks

### Block 0: P0 Protocol And Claim-Control Gate

- **Claim tested**: The dissertation wording matches the evidence and does not introduce protocol leakage or deployment overclaims.
- **Why this block exists**: The highest-risk supervisor criticism is not a new algorithmic gap; it is that the thesis might describe validation/test selection, model comparison, cost decisioning, and selective deployment too strongly.
- **Dataset / split / task**: No rerun. Review D-CRED code, `CLAIMS_FROM_RESULTS.md`, `AUTO_REVIEW.md`, result CSVs, and thesis draft text.
- **Compared systems**: Not applicable.
- **Metrics**: Claim-audit checklist, protocol-audit checklist.
- **Setup details**:
  - Confirm calibration fitting and selection use validation Brier.
  - Explicitly state test Brier is used for reporting only.
  - State validation reuse for calibration, threshold selection, and conformal quantile estimation.
  - State RF is LightGBM random-forest mode and RF/XGB use a stratified 50k fit cap.
  - State reviewed cases incur review cost only and no residual manual-review error.
  - State temporal AUC is not lower than random AUC in the current result.
  - State feature audit is a curated application-time protocol, not a contaminated-feature stress test.
- **Success criterion**: No thesis paragraph claims new SOTA, production-bank validity, high-automation lending approval, fairness compliance, reject inference, or test-set-driven model/calibration selection.
- **Failure interpretation**: If any of these claims appear, the dissertation becomes vulnerable at defense even if experiments are correct.
- **Table / figure target**: Main text limitation box; protocol summary table in Chapter 4; claim-boundary paragraph in Chapter 6.
- **Priority**: MUST-RUN / P0.
- **Run type**: Writing/protocol audit only; no new experiment.

### Block 1: Temporal Drift Attribution

- **Claim tested**: Temporal evaluation changes the operating environment in interpretable ways.
- **Why this block exists**: Current C1 is defensible but thin. Supervisor feedback asks: what changed between train/validation/test periods?
- **Dataset / split / task**: Lending Club temporal 60/20/20 split. Compare train, validation, and test partitions.
- **Compared systems**: No model comparison; dataset-level analysis only.
- **Metrics**:
  - Default rate by partition and quarter.
  - PSI for numeric and categorical application-time features.
  - KS statistic for numeric features.
  - Optional categorical distribution divergence for `purpose`, `home_ownership_n`, `addr_state`, `zip_code`, and `emp_length`.
- **Setup details**:
  - Use only the existing allowed features from `feature_audit_lending_club.csv`.
  - Use train as reference and compare validation/test against train.
  - Bucket numeric features with quantile bins fitted on train.
  - Report direction, not causal claims.
- **Success criterion**: At least one concise table identifies whether observed drift is mainly base-rate shift, feature-distribution shift, or both.
- **Failure interpretation**: If feature distributions barely change, C1 becomes a concept-drift or label-base-rate story; do not force covariate-shift claims.
- **Table / figure target**: Chapter 5 temporal analysis table; appendix PSI/KS table.
- **Priority**: MUST-RUN / P1.
- **Run type**: New analysis, no model retraining.

### Block 2: Selective Decisioning Sensitivity And Reviewed-Cohort Diagnosis

- **Claim tested**: Split conformal selective decisioning is a conservative risk-control mechanism, and its high review rate can be explained rather than hidden.
- **Why this block exists**: The 91% review rate is the most visible weakness. The plan should turn it into a transparent trade-off analysis.
- **Dataset / split / task**: Lending Club temporal split, best validation-selected calibrated record per model.
- **Compared systems**:
  - Existing uncertainty-band selective decisioning.
  - Existing split-conformal selective decisioning.
  - Baselines: cost-aware threshold without review; all-review reference if cheaply computable.
- **Metrics**:
  - Automation rate.
  - Review rate.
  - Approval rate and automatic rejection rate.
  - Approved default rate.
  - Expected cost.
  - Coverage and q-hat for split conformal.
  - Feature summary of reviewed vs automatic cases.
- **Setup details**:
  - First reuse `outputs/review_round1_fix/selective_results.csv` for alpha and review-cost multiplier summaries.
  - If row-level review masks were not stored, add a diagnostic script that recomputes masks for the existing Lending temporal setup and writes cohort summaries only.
  - Cohort profile should compare reviewed, auto-approved, and auto-rejected groups on `fico_n`, `dti_n`, `loan_amnt`, `revenue`, `purpose`, and default rate.
- **Success criterion**: The dissertation can show a compact curve/table proving that the chosen operating point is review-heavy by design, not accidentally concealed.
- **Failure interpretation**: If every alpha remains review-heavy, C4 remains useful only as conservative risk control; this is acceptable for MSc if stated honestly.
- **Table / figure target**: Chapter 5 selective trade-off figure; appendix cohort-profile table.
- **Priority**: MUST-RUN / P1.
- **Run type**: Mostly result aggregation; possible diagnostic rerun without changing the method.

### Block 3: Manual-Review Residual-Error Sensitivity

- **Claim tested**: The selective decisioning conclusion is robust, or not robust, to relaxing the optimistic assumption that manual review has no residual error.
- **Why this block exists**: Current selective expected cost assumes reviewed cases incur only review cost. Examiners can reasonably challenge this.
- **Dataset / split / task**: Lending Club temporal split, selective-review decisions.
- **Compared systems**:
  - Original cost-only manual review assumption.
  - Residual manual-review error scenarios: 1%, 3%, 5%, and 10%.
  - Optional capacity/cost stress: review multiplier 0.05, 0.10, 0.20, 0.50.
- **Metrics**:
  - Adjusted expected cost.
  - Break-even residual-error rate where selective decisioning stops improving over cost-aware thresholding.
  - Automation and review rate remain reported beside cost.
- **Setup details**:
  - Prefer row-level recomputation if Block 2 diagnostic masks are available.
  - If only aggregate outputs are used, label the result as a sensitivity approximation and keep it in appendix.
  - Do not claim manual reviewers are empirically measured; this is a stress test.
- **Success criterion**: The paper can state whether the selective-cost story depends strongly on perfect manual review.
- **Failure interpretation**: If modest residual-error rates erase the benefit, C4 should be further weakened to "illustrates a conservative review-routing analysis" rather than "reduces expected cost in realistic review settings."
- **Table / figure target**: Chapter 6 sensitivity table or appendix stress-test table.
- **Priority**: MUST-RUN / P1.
- **Run type**: New sensitivity analysis, no model retraining.

### Block 4: Cost And Profit Scenario Consolidation

- **Claim tested**: Cost-aware decisioning is not merely a trivial win against fixed 0.5 under one hand-picked setting.
- **Why this block exists**: Supervisor feedback correctly notes that beating 0.5 is expected in asymmetric credit decisions. The dissertation should show broader scenario awareness without claiming full business validity.
- **Dataset / split / task**: Lending Club temporal split, existing decision outputs.
- **Compared systems**:
  - Fixed 0.5.
  - F1 validation threshold.
  - Cost ratio thresholds for available ratios.
  - Robust cost threshold.
  - Existing LGD/ROI profit-threshold scenarios.
- **Metrics**:
  - Expected cost under cost scenarios.
  - Approval/rejection rates.
  - Mean realized profit and mean expected profit for LGD/ROI scenarios.
  - Paired bootstrap deltas where already available.
- **Setup details**:
  - Reuse `outputs/review_round1_fix/decision_results.csv` and `decision_delta_ci.csv`.
  - Summarise, do not redesign the financial model.
  - Keep main claim tied to stated assumptions.
- **Success criterion**: The thesis can say cost-aware thresholding remains useful across reported scenarios, while full business ROI validity remains future work.
- **Failure interpretation**: If profit scenarios are unstable, keep C3 focused on expected-cost reduction under the FN:FP setting and move profit rows to appendix.
- **Table / figure target**: Chapter 5 cost-decision table; appendix LGD/ROI scenario table.
- **Priority**: MUST-RUN / P1.
- **Run type**: Result aggregation, no model retraining.

## Run Order And Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 | Lock P0 claim boundaries before more analysis | R001-R003 | No protocol or claim overstatement remains | 0.5 day writing/review | Draft may already contain overclaims; fix before adding new sections |
| M1 | Explain temporal shift | R101-R102 | PSI/KS table gives a defensible interpretation of train/test change | 1-3 CPU hours | Drift may be weak; write as diagnostic not proof |
| M2 | Make selective decisioning transparent | R201-R203 | Trade-off table clearly shows review-heavy behavior and cohort profile | 2-6 CPU hours, more if masks need recomputation | Row-level masks may not exist in current outputs |
| M3 | Stress manual-review assumption | R301-R302 | Sensitivity table states when C4 survives or fails | 1-3 CPU hours | Benefit may disappear under realistic reviewer error |
| M4 | Consolidate cost/profit evidence | R401-R402 | Existing scenarios are summarized without overclaiming business ROI | 1 CPU hour | Profit assumptions may be too synthetic; keep appendix if needed |
| M5 | Integrate into dissertation | R501-R503 | All tables map to claim boundaries and limitations | 0.5-1 day writing | More tables can dilute story; keep main text compact |

## Compute And Data Budget

- **Total estimated GPU-hours**: 0 by default. GPU is only needed if the diagnostic script reruns model predictions instead of reusing existing outputs.
- **Total estimated CPU time**: 4-12 hours including scripting, aggregation, and figure/table generation.
- **Data preparation needs**: Existing Lending Club processed data and `outputs/review_round1_fix/` results.
- **Human evaluation needs**: None.
- **Biggest bottleneck**: Whether selective review masks and per-case probabilities can be reconstructed cleanly for reviewed-cohort and residual-error diagnostics.

## Risks And Mitigations

- **Risk**: P1 analyses reveal weaker support for C4.
  - **Mitigation**: Treat that as useful dissertation evidence; C4 is already partial and should remain conservative.
- **Risk**: PSI/KS does not show strong covariate shift.
  - **Mitigation**: Report base-rate and calibration/threshold drift rather than forcing a covariate-shift claim.
- **Risk**: Review-mask reconstruction requires too much code.
  - **Mitigation**: Use aggregate alpha/review-cost sensitivity as main text; move cohort profile to optional appendix.
- **Risk**: Cost/profit scenarios look synthetic.
  - **Mitigation**: Label them scenario analyses and keep the primary C3 claim on FN:FP expected cost with paired delta CI.
- **Risk**: Extra experiments make thesis look unfocused.
  - **Mitigation**: Main chapter gets only one table/figure per claim; detailed diagnostics go to appendix.

## Must-Run Versus Nice-To-Have

Must-run:

- B0 P0 protocol and claim-control gate.
- B1 temporal drift attribution.
- B2 selective sensitivity table.
- B3 manual-review residual-error sensitivity.
- B4 cost/profit scenario consolidation.

Nice-to-have if time remains:

- Reviewed-cohort visual profile figure.
- All-review reference cost.
- Additional alpha points beyond existing defaults.
- Subgroup calibration by FICO/income-like bins.

Cut from this plan:

- Rolling-window OOT validation.
- Full fairness compliance.
- Reject-inference correction.
- New external datasets.
- Full SHAP explainability.
- Dynamic instance-level financial model redesign.

## Final Checklist

- [ ] P0 claim audit completed before drafting final results chapter.
- [ ] Calibration source selection described as validation-based, not test-based.
- [ ] Validation reuse limitation appears in methods and discussion.
- [ ] Temporal shift table supports only a bounded deployment-setting claim.
- [ ] Selective decisioning table reports automation, review rate, and expected cost together.
- [ ] Manual-review residual-error sensitivity is included or explicitly deferred.
- [ ] Cost/profit scenario summary avoids production-bank ROI claims.
- [ ] P2/P3 items are listed as limitations/future work, not active blockers.

