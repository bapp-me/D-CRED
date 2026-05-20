# Raw Debate Ruling - Blind Review Nightmare Round 1

Reviewer: primary memory-carrying nightmare reviewer
Date: 2026-05-20

## Weakness #1: `locked_final_protocol` is not a true post-freeze rerun

Ruling: `accepted`

The reviewer accepted the rebuttal. The current evidence supports only a retrospective selected-only protocol audit, not a pristine rerun. `DONE_REUSED` in the tracker, old source-run mtimes in `protocol_manifest.json`, and `frozen_config.yaml` pointing to old directories are sufficient to classify this limitation.

Resolved for MSc writing: yes, but only as limitation/disclosure.

Resolved for blind-review Point 2 closure: no.

Minimum change:

- Immediately rename/rewrite this evidence as `retrospective selected-only protocol audit`.
- State that Point 2 is partially mitigated, not closed.
- A true closure requires a new run launched from a frozen artifact with preserved pre-final-test evidence.

## Weakness #2: cash-flow layer is a negative result

Ruling: `accepted`

The reviewer accepted the rebuttal. The evidence supports a negative/mixed cash-flow conclusion: `cashflow_coverage_constrained_best_policy.csv` selects `pd_risk_ranking` at every target approval rate, and `cashflow_model_metrics.csv` retains negative final-test cash R2.

Resolved for MSc writing: yes, if cash-flow is downgraded to negative/mixed decision-analysis evidence.

Minimum change:

- Rewrite A5 as "objective change exposes constrained frontier; learned cash ranking currently weak/negative".
- Do not write that the cash objective improves anything.
- Move cash-flow into mixed evidence/results discussion rather than a main contribution win.

## Weakness #3: responsible-credit / feature audit evidence is too shallow

Ruling: `partially accepted`

The reviewer accepted the downscoping, but not full closure. Current evidence supports a proxy-group risk-exposure audit, a header-level field catalog, and capped sanity stress only.

Resolved for MSc writing: yes, but only as appendix/limitation evidence.

Resolved for blind-review Points 8/11 closure: no.

Minimum evidence needed for closure:

- Direct full-data with-zip versus without-zip table.
- Policy-conditioned utility and realized-cost columns.
- Full-data same-model strict/default/expanded comparison, or explicit abandonment of closure language.

## Overall Ruling

If the question is whether the project can proceed to MSc thesis writing without more experiments, the answer is `almost / limited ready`.

Hard conditions:

1. Point 2 must be written as retrospective hygiene plus remaining limitation, not solved.
2. Cash-flow must be written as negative/mixed decision analysis, not a positive contribution layer.
3. Responsible-credit and feature audit must be written as minimum risk-exposure appendix and sanity evidence, not blind-review closure.
4. Thesis, handoff, and claim-control must be synchronized to the downgraded claims.

If those conditions are not implemented, the ruling remains `not ready`.
