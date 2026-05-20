# Dean Cash-Flow Experiment Plan

**Problem**: The previous D-CRED main evidence uses normalized FN/FP/review-cost assumptions. The dean's review argues that the stronger MSc contribution is to replace those assumptions with observed Lending Club loan cash flows and to model review as costly information acquisition.

**Method Thesis**: D-CRED should be reframed as empirically anchored credit decisioning: use application-time features to predict default and/or loan-level net cash, then decide approve/deny/review under review-cost and capacity constraints. Review means paying to acquire additional credit-bureau or verification features, not assuming a magical human residual error.

**Date**: 2026-05-19

## Data Scope

Primary data source:

- `data/raw/lending_club/loan.csv`

Main sample:

- Terminal accepted loans only:
  - good: `Fully Paid`, `Does not meet the credit policy. Status:Fully Paid`
  - bad: `Charged Off`, `Default`, `Does not meet the credit policy. Status:Charged Off`
- Excluded from main cash-flow evaluation:
  - `Current`, `Late`, `In Grace Period`, and other non-terminal states because repayment cash flow is censored.

Outcome construction:

```text
net_cash =
  total_rec_prncp
  + total_rec_int
  + total_rec_late_fee
  + recoveries
  - funded_amnt
  - collection_recovery_fee
```

`net_cash`, repayment totals, recoveries, and `loan_status` are outcome fields. They must not enter the application-time feature models.

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: Loan-level cash-flow utility changes the decision objective relative to binary default costs. | This is the dean's first two proposed contributions: cash-flow outcomes and example-dependent costs. | Direct cash model or tuned PD policy improves realized net cash per 1000 loans over fixed default threshold, while reporting rejected-profitable-loan opportunity cost and approved-loss-making-loan loss. | B1 |
| C2: Budgeted information acquisition is implementable and can be compared against uncertainty/conformal review. | This replaces abstract human residual error with a concrete review mechanism. | Cheap-feature model, full-feature model, predicted VOI ranker, uncertainty baseline, conformal-style baseline, random review, and stylized D-CRED benefit ranking all evaluated on the same final test. | B2, B3 |
| C3: Cost sensitivity is explicit instead of hidden in one arbitrary review-cost point. | This answers the dean's demand for review-cost and robustness matrices. | Review-cost grid and capacity grid report realized utility, expected utility, review ROI, and sensitivity to loss/profit scaling. | B4 |

## Paper Storyline

Main paper must prove:

- The new accepted-loan cash-flow dataset supports observed loan-level profit/loss labels.
- Cash-flow fields are used only as outcomes, not predictors.
- Direct expected net-cash decisioning is a meaningful alternative to fixed default thresholds.
- Review capacity can be allocated by predicted value of information and compared honestly against uncertainty, conformal-style, random, and old D-CRED-style ranking baselines.
- Sensitivity to review cost and loss/profit stress is visible rather than hidden.

Appendix can support:

- Full feature audit.
- Review-cost grid derived from wage/time/overhead assumptions.
- Loss/profit ratio stress tests.
- Month-blocked split table.
- Existing `reject_capacity_month_blocked` result as continuity with the earlier D-CRED narrative.

Experiments intentionally cut:

- Full rejected-applicant population inference; `loan.csv` is an accepted/funded loan book.
- Claims about real human reviewer accuracy.
- Production bank ROI or causal policy deployment.
- FICO-specific claims, because this `loan.csv` header does not expose FICO fields.

## Experiment Blocks

### Block 1: Economic Utility Decisioning

- **Claim tested**: Observed loan-level net cash supports a stronger decision objective than binary default alone.
- **Why this block exists**: The dean explicitly asks to replace `FN:FP=5:1` with loan-level cash flow and example-dependent costs.
- **Dataset / split / task**: Terminal Lending Club accepted loans; month-blocked seven-role split.
- **Compared systems**:
  - Fixed PD threshold `p(default)<0.5`.
  - PD threshold tuned on `policy_tune` to maximize realized net cash.
  - Direct cash-flow regression decision: approve if predicted `net_cash>0`.
- **Metrics**:
  - Mean realized utility per application.
  - Realized utility per 1000 applications.
  - Approval rate.
  - Accepted-loan realized profit/loss.
  - Rejected profitable-loan opportunity cost.
  - Approved loss-making-loan loss.
  - PD AUC/Brier and cash-regression MAE/RMSE/R2.
- **Setup details**:
  - PD model predicts terminal bad loan.
  - Cash model predicts `net_cash`.
  - Policy tuning uses `policy_tune`, final reporting uses `final_test`.
- **Success criterion**: At least one cash-flow-aware decision policy improves realized utility over fixed threshold and makes opportunity/loss trade-offs explicit.
- **Failure interpretation**: If fixed threshold is competitive, the result still demonstrates the economic cost profile and should narrow claims.
- **Table / figure target**: Main results table for economic utility.
- **Priority**: MUST-RUN.

### Block 2: Two-Stage Information Acquisition

- **Claim tested**: Review can be modeled as paying for additional information.
- **Why this block exists**: This is the dean's replacement for abstract human residual `rho`.
- **Dataset / split / task**: Same terminal Lending Club sample.
- **Compared systems**:
  - `M0`: cheap features only.
  - `M1`: cheap + review/credit features.
  - `g(x_cheap)`: predicted value-of-information scorer.
- **Feature groups**:
  - Cheap features: loan amount, funded amount, term, annual income, employment length, purpose, home ownership, state, ZIP prefix.
  - Review/full features: cheap features plus verification status, DTI, delinquency, inquiries, revolving utilization, open accounts, public records, total accounts, credit-balance/utilization fields available in `loan.csv`.
- **Metrics**:
  - Utility difference between cheap and full decisioning.
  - Predicted VOI quality by downstream capacity frontier, not just regression error.
- **Setup details**:
  - Full features are available offline to train the upper-stage model.
  - At deployment, review is simulated by selecting cases using `g(x_cheap)`, then applying the full-feature cash decision after paying review cost.
- **Success criterion**: The two-stage mechanism produces parseable and interpretable utility-frontier results.
- **Failure interpretation**: If predicted VOI loses to uncertainty review, this becomes a useful boundary condition.
- **Table / figure target**: Method table plus review frontier.
- **Priority**: MUST-RUN.

### Block 3: Review Capacity Frontier

- **Claim tested**: The policy-level value comes from allocating limited review capacity, not unlimited review.
- **Why this block exists**: The old unrestricted reject option degenerates to near all-review.
- **Dataset / split / task**: Final test terminal accepted loans.
- **Compared systems**:
  - no review cheap model
  - all review full model
  - random review
  - uncertainty review
  - conformal interval crossing review
  - old D-CRED stylized benefit ranking
  - predicted value-of-information review
  - oracle value-of-information upper bound
- **Capacity grid**: `1%, 2%, 5%, 10%, 20%, 30%, 50%`.
- **Metrics**:
  - expected utility
  - realized utility
  - realized utility per 1000 applications
  - review rate
  - approval rate
  - opportunity cost of rejected profitable loans
  - approved loss-making loan loss
  - review ROI per dollar
- **Setup details**:
  - Primary review cost is `$10`.
  - Conformal-style review uses residual calibration of the cheap cash model and reviews cases whose prediction interval crosses zero, constrained by capacity.
- **Success criterion**: Predicted VOI is competitive with uncertainty/conformal baselines or identifies where it fails.
- **Failure interpretation**: Preserve negative/mixed results and write boundary conditions.
- **Table / figure target**: Capacity frontier curve/table.
- **Priority**: MUST-RUN.

### Block 4: Review-Cost And Robustness Matrix

- **Claim tested**: The conclusion is not an artifact of a single review-cost point.
- **Why this block exists**: The dean explicitly asks for review-cost and robustness grids.
- **Dataset / split / task**: Same final test predictions, evaluated under multiple costs and stress labels.
- **Compared systems**:
  - uncertainty review
  - predicted VOI review
  - old D-CRED stylized benefit ranking
  - no review and all review references
- **Cost grid**:
  - direct review costs: `$5, $10, $20, $30, $50, $100`
  - wage-derived grid: minutes `{5,10,20,30}` and overhead `{1.0,1.3,1.5,2.0}` using a configurable hourly wage
  - loss/profit stress ratios `{1,2,5,10,11.4,15,20}`
- **Metrics**:
  - realized utility and review ROI by cost/capacity
  - policy rank changes
  - sensitivity of approved loss-making loans and rejected profitable loans
- **Setup details**:
  - Direct cost grid is required.
  - Wage-derived grid is recorded as a configurable anchor; source verification belongs in the writing/audit pass.
  - Loss/profit stress rescales negative realized cash-flow losses while preserving positive profits.
- **Success criterion**: The result table shows when VOI, uncertainty, or no-review policies dominate.
- **Failure interpretation**: If policy ranking is unstable, the thesis should emphasize decision analysis rather than a single universal winner.
- **Table / figure target**: Heatmap and sensitivity appendix.
- **Priority**: MUST-RUN.

## Run Order And Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 | Build terminal loan cash-flow dataset | C001-C004 | Cash-flow fields present and censored rows excluded | CPU minutes | Status mapping or date parsing could be wrong |
| M1 | Economic utility baselines | C101-C103 | Fixed PD, tuned PD, and cash regression policies produce final-test metrics | CPU minutes to hours | Cash regression may be noisy |
| M2 | Two-stage models and VOI scorer | C201-C204 | Cheap/full decisions and VOI scores saved | CPU minutes to hours | VOI prediction may be weak |
| M3 | Capacity frontier | C301-C308 | Review baselines evaluated over capacity grid | CPU minutes | All-review may be dominated by review cost |
| M4 | Cost and robustness sensitivity | C401-C404 | Review-cost and loss/profit grids saved | CPU minutes | Large table may need careful summarization |
| M5 | Write results and claim guardrails | C501-C503 | Results, tracker, and handoff update written | CPU minutes | Overclaiming economic deployment |

## Compute And Data Budget

- Expected GPU-hours: 0. This plan uses scalable CPU linear models first.
- Expected CPU time: minutes to a few hours on the full terminal sample.
- Data preparation needs: read selected columns from a 1.19 GB CSV; use terminal rows only.
- Human evaluation needs: none.
- Biggest bottleneck: preserving clean feature/outcome separation and not overclaiming accepted-loan evaluation as full applicant-population deployment.

## Risks And Mitigations

- **Censored loans**: exclude non-terminal statuses from the main experiment.
- **Outcome leakage**: cash-flow, hardship, settlement, last-payment, and loan-status fields are outcomes or post-origination fields and must not enter features.
- **Accepted-loan selection bias**: state clearly that this is funded-loan policy evaluation, not rejected-applicant inference.
- **FICO field absent**: use available credit-history fields as review features; do not claim FICO-specific evidence.
- **Weak VOI result**: preserve mixed results and compare to uncertainty baselines.

## Final Checklist

- [x] Terminal sample summary written.
- [x] Cash-flow distribution table written.
- [x] Feature audit written.
- [x] Economic utility policy table written.
- [x] Cheap/full acquisition frontier written.
- [x] Review-cost sensitivity grid written.
- [x] Loss/profit stress grid written.
- [x] Results summary written.
- [x] Claim caveats written.
