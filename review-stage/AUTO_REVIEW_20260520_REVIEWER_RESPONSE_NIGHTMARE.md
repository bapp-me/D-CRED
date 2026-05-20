# Nightmare Auto Review - Reviewer-Response Experiments

Timestamp: 2026-05-20T00:16:14+08:00

Mode: `auto-review-loop`, difficulty `nightmare`

Scope:

- Advisor strict month-blocked temporal split.
- Dean observed cash-flow and budgeted feature-acquisition experiments.
- Authoritative dean evidence: `refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md` and `outputs/dean_cashflow_full/`.
- Explicit guardrail: the dean full run supersedes the earlier proxy-only pilot.

## Assessment Summary

- MSc score: `6.5-7/10`.
- Top-tier ML score: `1.5-2/10`.
- Overall verdict: `almost` for MSc after targeted repair; `not ready` for top-tier ML.
- Advisor response: `ready` for dissertation use.
- Dean response: `almost`, but scientifically weakened until the `funded_amnt` predictor/audit contradiction is fixed and the full run is regenerated.

## Key Findings

1. The advisor's month-blocked critique is addressed for the core MSc claim. Both reviewers accepted that the month audit is clean, the selected calibrated source remains `lgbm/sigmoid`, and the capacity frontier remains monotone under strict issue-month blocking.

2. The dean full run resolves the earlier proxy-only limitation: `loan.csv` contains observed repayment fields, the run uses terminal accepted loans, and final-test policy utility is computed from observed net cash.

3. The dean run has one serious protocol contradiction. `funded_amnt` is included in `CHEAP_NUMERIC` while also used in cash-flow construction and labeled as disallowed in the feature audit. The written claim that cash-flow/post-origination fields are never predictors is therefore false as written.

4. The cash-flow evidence supports policy comparison more strongly than accurate expected-cash prediction. Final-test cash regression has negative `R^2`; tuned cash utility wins by becoming very conservative, with approval rate around `0.71%` and high missed-profitable-loan opportunity cost.

5. Predicted VOI is a negative result. It selects zero reviews under the primary final-test setting. The strongest non-oracle review rule is conformal interval review near the tuned cash-decision boundary.

6. Review benefit is regime-dependent. Conformal review is positive in high-loss regimes and selected capacities, but not across the full cost-capacity or loss/profit grids.

7. Stale proxy-only handoff material remains a writing risk. The advisor writing update and advisor experiment result still contain superseded dean-pilot statements; future writing must route dean claims through `DEAN_CASHFLOW_EXPERIMENT_RESULTS.md` and `outputs/dean_cashflow_full/`.

## Debate Ruling

- `funded_amnt` contradiction: **accepted**, unresolved blocker.
- Advisor month-blocked critique: **accepted**, resolved for the supervisor's stated MSc-level concern.
- Dean cash-flow and review frontier: **partially accepted**, only narrow accepted-loan cash-flow claims are supportable before repair.
- Stale proxy-only handoff risk: **accepted**, unresolved writing blocker.

## Minimum Fixes

MSc required:

1. Remove `funded_amnt` from predictor groups and rerun `dean_cashflow_full`, or explicitly reframe the dean experiment as post-funding analysis and rewrite the audit/prose accordingly.
2. Mark proxy-only dean sections in `ADVISOR_REVIEW_EXPERIMENT_RESULTS.md` and `ADVISOR_REVIEW_WRITING_UPDATE_20260519.md` as superseded.
3. Narrow dean claims to accepted/funded-loan policy evaluation, tuned cash vs PD threshold comparison, and conformal interval review as the best non-oracle acquisition rule in this run.
4. Put the low approval rate, missed-profit opportunity cost, funded-loan-only scope, and no-real-human-review caveats in the main text.

Top-venue required:

1. Rerun with leakage-clean feature groups and a realized-incremental-utility VOI target.
2. Add stronger matched review baselines and rolling or multi-window temporal backtests.
3. Add another dataset or explicitly solve accepted-loan selection/reject-inference scope.
4. Establish a genuine method contribution beyond a useful decision-analysis framework.

## Method Description

D-CRED's current defensible dissertation method is a deployment-oriented credit-risk decision-analysis pipeline. It trains calibrated PD and cash-flow decision models under strict role-separated temporal protocols, evaluates approve/deny/review policies on locked future periods, and reports cost or utility frontiers under explicit review-capacity and review-cost constraints.

The latest reviewer-response evidence has two branches. The advisor branch strengthens temporal isolation through issue-month-blocked seven-role splitting and validates that the calibrated capacity frontier is qualitatively stable. The dean branch uses observed Lending Club accepted-loan repayment fields to construct net-cash utility and compares no-review, full-review, conformal interval review, stylized D-CRED ranking, predicted VOI, and oracle VOI policies under budgeted acquisition. This branch is promising for MSc framing but requires a clean rerun after the `funded_amnt` feature-separation fix.

## Raw Responses

- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_BEAUVOIR_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_ERDOS_20260520.md`
- `review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_DEBATE_20260520.md`

## Status

Completed as a nightmare review round. No code changes were made. The main recommended next step is a focused repair/rerun of the dean cash-flow experiment, not a broad new research pivot.
