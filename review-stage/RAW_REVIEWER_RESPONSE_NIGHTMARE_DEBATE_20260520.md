# Raw Reviewer Ruling - Nightmare Debate - Beauvoir

Reviewer agent id: `019e40f3-a991-7d83-82ad-4d33e4055deb`

**Ruling**

1. `funded_amnt` feature-separation contradiction: **Accepted**.
   The response is substantively correct. The contradiction is real in [cashflow_feature_acquisition_experiment.py](</D:/code/diss_codex/D-CRED/scripts/cashflow_feature_acquisition_experiment.py:54>) and it conflicts with both the emitted audit in [feature_audit_loan_csv.csv](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/feature_audit_loan_csv.csv:5>) and the written claim in [EXPERIMENT_RESULTS.md](</D:/code/diss_codex/D-CRED/outputs/dean_cashflow_full/EXPERIMENT_RESULTS.md:111>).
   One tightening: if this count is quoted in the dissertation, recompute and report it on the exact evaluation cohort; my verified terminal-sample check was `2062 / 1306387`, not the raw-file count.

2. Advisor month-blocked temporal critique: **Accepted**.
   This is resolved for the supervisor's stated MSc-level concern. The month audit is clean, the selected source is unchanged, and the frontier remains monotone in [reject_capacity_month_blocked/EXPERIMENT_RESULTS.md](</D:/code/diss_codex/D-CRED/outputs/reject_capacity_month_blocked/EXPERIMENT_RESULTS.md:28>) with negligible row-vs-month deltas in [ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv](</D:/code/diss_codex/D-CRED/refine-logs/ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv).
   The remaining limit is claim scope only: do not sell unrestricted reject-option dominance when it still reviews `99.17%`.

3. Dean cash-flow claims and review frontier: **Partially accepted**.
   The response is right that the proxy-only limitation is gone and a narrow accepted-loan cash-flow claim is now supportable. It is also right that learned VOI is not supported.
   **Minimum change required:** rerun the dean cash-flow experiment after removing `funded_amnt` from predictors, then keep the claim to:
   - accepted/funded-loan policy evaluation only,
   - tuned cash policy beats fixed/tuned PD thresholds under this net-cash objective,
   - conformal interval review is the strongest non-oracle review rule in this run,
   - learned VOI is a negative result,
   - review benefit is regime-dependent, not universal.
   Without that rerun, the dean-response evidence remains scientifically weakened.

4. Stale handoff / proxy-only contamination: **Accepted**.
   This is a real handoff-risk issue. [ADVISOR_REVIEW_WRITING_UPDATE_20260519.md](</D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/ADVISOR_REVIEW_WRITING_UPDATE_20260519.md:31>) can still mislead a fresh writing model, while [DEAN_CASHFLOW_WRITING_UPDATE_20260519.md](</D:/code/diss_codex/paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260519.md:5>) explicitly says it supersedes that older path. Mark the proxy-only sections as superseded or obsolete and route dean-side claims to the new dean result bundle.

**Updated Memory Update**

- Persistent suspicion: the dean cash-flow experiment is still not clean until `funded_amnt` is removed from predictors or the task is explicitly reframed as post-funding analysis.
- Unresolved concern: cash regression quality is weak enough that policy comparison is safer than any claim about accurate expected net-cash prediction.
- Claim boundary: advisor-response evidence is strong enough for MSc defense on temporal protocol robustness.
- Claim boundary: dean-response evidence supports a narrow accepted-loan, observed-cash-flow decision-analysis story; it does not support a learned-VOI win or a top-tier ML contribution claim.
