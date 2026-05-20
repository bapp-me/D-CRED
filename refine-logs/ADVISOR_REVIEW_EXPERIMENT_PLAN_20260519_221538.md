# Advisor Review Experiment Plan

**Problem**: The current D-CRED MSc thesis needs to answer two new review pressures: the supervisor's concern that row-wise chronological roles still share boundary months, and the dean's concern that the review-cost story is too stylized to count as an economic contribution.

**Method Thesis**: The immediate defensible repair is a strict month-blocked rerun of the existing calibrated PD + reject option + capacity frontier. The larger economic direction should be implemented only as a scoped pilot on the current granting dataset, because this checkout does not contain observed repayment cash-flow fields.

**Date**: 2026-05-19

## Review Advice Triage

| Source | Advice | Experimental Decision |
|---|---|---|
| Supervisor review | Use month-blocked seven-role temporal isolation and rerun reject-capacity. | MUST-RUN now. This directly attacks the period-level contamination objection. |
| Supervisor review | Rolling-window is useful but not minimum necessary. | NICE-TO-HAVE appendix only. Do not delay the MSc repair. |
| Dean review | Replace normalized FN/FP costs with loan-level cash-flow utility. | SHOULD-RUN only after a cash-flow Lending Club dataset is added. Current granting CSV lacks `total_pymnt`, `recoveries`, and `collection_recovery_fee`. |
| Dean review | Model review as costly information acquisition with cheap vs full features. | MUST-RUN as a proxy pilot using current fields: cheap application features vs acquired credit features. |

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: Month-blocked temporal isolation does not break the main D-CRED capacity-frontier story. | Fixes the supervisor's period-level contamination concern. | `month_boundary_audit.csv` shows no shared `issue_d` month across roles; selected source and capacity frontier remain qualitatively stable. | B1, B2 |
| C2: Capacity-aware deferral remains the correct main result, not unrestricted reject-option dominance. | Preserves the existing claim boundary and avoids all-review overclaiming. | Capacity cost decreases monotonically from small to larger review budgets; unrestricted review remains near all-review. | B2 |
| C3: The dean's economic direction is implementable, but current evidence is proxy utility rather than observed bank cash flow. | Converts a thesis weakness into a future contribution without fabricating data. | A cheap/full feature acquisition pilot produces frontier tables and explicitly labels the missing cash-flow blocker. | B3 |

## Paper Storyline

Main paper must prove:

- The new main Lending Club protocol is month-blocked at the natural-month level.
- The selected calibrated source is chosen on `calibration_select`, with selected-only final-test reporting.
- The capacity frontier is stable under stricter temporal isolation.
- The economic utility and feature-acquisition direction is a scoped extension, not a replacement for the current completed MSc evidence unless true cash-flow data are added.

Appendix can support:

- Row-wise vs month-blocked comparison.
- Proxy utility and feature-acquisition pilot tables.
- Rolling-window evaluation if time permits.
- Public cost anchors for future writing, after source verification.

Experiments intentionally cut:

- Production-bank ROI claims.
- Observed loan-level cash-flow claims without a new dataset.
- Formal active feature acquisition optimality claims.
- Top-venue novelty claims.

## Experiment Blocks

### Block 1: Month-Blocked Seven-Role Split

- **Claim tested**: Each natural `issue_d` month belongs to exactly one experiment role.
- **Why this block exists**: Row-wise chronological splits can share macro conditions across adjacent roles.
- **Dataset / split / task**: Lending Club granting dataset; `model_train / model_dev / calibration_fit / calibration_select / policy_tune / risk_calibration / final_test`.
- **Compared systems**: Not applicable.
- **Metrics**: Role row counts, default rates, start/end months, number of issue months, month-sharing audit.
- **Setup details**: Add `--role-split-mode month`; write `month_boundary_audit.csv`.
- **Success criterion**: Every row in the audit has `n_roles = 1`.
- **Failure interpretation**: If role sizes become unusable, fall back to row-wise split with explicit limitation.
- **Table / figure target**: Chapter 4 protocol table.
- **Priority**: MUST-RUN.

### Block 2: Month-Blocked Reject-Capacity Rerun

- **Claim tested**: The main capacity frontier is robust to stricter temporal isolation.
- **Why this block exists**: This is the supervisor's minimum requested repair.
- **Dataset / split / task**: Same Lending Club data, month-blocked role split.
- **Compared systems**: LR, LightGBM, XGBoost calibrated candidates; no-review, all-review, unrestricted reject option, capacity-aware deferral, uncertainty band, split conformal, empirical risk-control baseline.
- **Metrics**: Brier/ECE/NLL; selected model/calibrator; expected cost; realized cost; review rate; automation rate; savings vs no-review and all-review.
- **Setup details**: Use no tree row cap, selected-only final-test reporting, primary scenario FN:FP=5:1, review cost=0.10, rho=0.10.
- **Success criterion**: Selected source remains credible and capacity-aware expected cost is monotone decreasing as review budget rises.
- **Failure interpretation**: If gains weaken, write that the frontier remains informative but quantitatively sensitive to temporal blocking.
- **Table / figure target**: Chapter 5 month-blocked robustness table.
- **Priority**: MUST-RUN.

### Block 3: Proxy Economic Utility And Feature Acquisition Pilot

- **Claim tested**: The dean's proposed two-stage information acquisition design can be implemented with current code, but only as proxy evidence.
- **Why this block exists**: The current dataset has no observed loan cash-flow columns, so the full dean direction cannot honestly be completed from existing files.
- **Dataset / split / task**: Lending Club granting dataset; month-blocked roles; cheap features vs full features.
- **Compared systems**: No review cheap model, all review full model, random review, uncertainty review, predicted value-of-information review, oracle value-of-information upper bound.
- **Metrics**: Mean expected proxy utility, mean realized proxy utility, utility per 1000 applications, review rate, approval rate, opportunity cost, approved-default loss, lift per review dollar.
- **Setup details**: Cheap features are application-level fields; full features add available credit signals such as `fico_n` and `dti_n`. Utility uses `loan_amnt` with ROI=0.10 and LGD=0.60 because observed repayment cash flows are absent.
- **Success criterion**: The output frontier is parseable and gives a bounded interpretation of whether value-of-information ranking helps under proxy utility.
- **Failure interpretation**: If predicted VOI does not beat uncertainty review, write it as a negative boundary result and keep the dean direction as future work requiring richer data.
- **Table / figure target**: Appendix pilot table or future-work evidence.
- **Priority**: MUST-RUN, scoped.

### Block 4: True Loan-Level Cash-Flow Upgrade

- **Claim tested**: D-CRED can be reframed around observed loan-level profit/loss.
- **Why this block exists**: This is the dean's strongest proposed novelty path.
- **Dataset / split / task**: A Lending Club accepted-loan dataset with repayment columns, not the current granting CSV.
- **Compared systems**: Default threshold, cost-sensitive threshold, direct expected net cash, budgeted feature acquisition.
- **Metrics**: Profit per 1000 applications, accepted-loan realized profit/loss, rejected profitable-loan opportunity cost, approved loss-making-loan loss, review ROI.
- **Setup details**: Requires adding and auditing cash-flow outcome fields that are not application-time features.
- **Success criterion**: Observed cash-flow fields exist and are used only as outcomes, never as application-time predictors.
- **Failure interpretation**: Without those fields, the thesis must not claim observed economic utility.
- **Table / figure target**: Future main contribution table.
- **Priority**: SHOULD-RUN, currently BLOCKED by dataset schema.

## Run Order And Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 | Parse advisor reviews and freeze claim scope | A001-A003 | Must-run vs blocked work separated | <1 hour | Over-expanding thesis scope |
| M1 | Implement month-blocked split | M101-M103 | Audit proves no shared month | CPU minutes | Small sample sanity fails if it contains too few months |
| M2 | Rerun reject-capacity under month blocking | M201-M204 | Capacity frontier remains monotone | ~1 hour local CPU/GPU | XGBoost CUDA warning may fall back for prediction only |
| M3 | Compare row-wise vs month-blocked results | M301 | Selected source and main costs are stable | CPU minutes | Quantitative deltas could weaken the story |
| M4 | Run proxy utility and feature acquisition pilot | E101-E304 | Outputs are parseable and caveated | CPU minutes | Proxy utility is not true cash flow |
| M5 | True cash-flow upgrade | E901 | Required fields are present | Unknown | Dataset not currently available |

## Compute And Data Budget

- GPU-hours used: near zero to light RTX 4060 use; XGBoost training completed with CUDA configured and a prediction-device warning only.
- Data preparation: no new public downloads were required.
- Biggest bottleneck: true dean-level cash-flow evidence is blocked by the current CSV schema.

## Risks And Mitigations

- **Risk**: Month-blocked final test has a different default rate and could change the conclusion.
- **Mitigation**: Report the changed role default rates directly; do not hide quantitative sensitivity.

- **Risk**: Proxy utility is mistaken for observed bank economics.
- **Mitigation**: Every output names it as proxy utility and records the missing cash-flow fields.

- **Risk**: Predicted value-of-information ranking underperforms uncertainty review.
- **Mitigation**: Preserve this as a negative or mixed result; do not force a win claim.

## Final Checklist

- [x] Main paper month-blocked robustness is covered.
- [x] Month boundary audit proves no shared issue month.
- [x] Selected-only final-test reporting is available for the new month-blocked run.
- [x] Row-wise vs month-blocked comparison is written.
- [x] Proxy feature-acquisition pilot is complete.
- [x] True cash-flow upgrade is separated as blocked, not fabricated.
