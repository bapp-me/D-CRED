# Review Trace - Reject-Option Capacity Round 1

Date: 2026-05-19

## Route

- Reviewer backend: Codex sub-agent
- Reviewer model: gpt-5.4
- Reasoning effort: xhigh
- Difficulty: hard
- Agent id: `019e3c11-9d22-7f40-92db-59d74aea25ac`

## Prompt Summary

The reviewer was asked to audit the new D-CRED reject-option and capacity-aware rerun, prioritizing:

- `refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_PLAN.md`
- `refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_RESULTS.md`
- `refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_TRACKER.md`
- `refine-logs/EXPERIMENT_CODE_REVIEW.md`
- `outputs/reject_capacity_full/` split, protocol, calibration, final-decision, capacity-frontier, Venn-Abers fallback, and final-test access artifacts

Old outputs and old claim files were allowed only as historical contrast, not current evidence.

## Outcome

- MSc readiness: 8/10, almost ready.
- Top-venue readiness: 4/10, not ready.
- Main accepted fix: no 50k cap in the new main evidence.
- Main unresolved blocker: strict locked-final-test wording is too strong because all-candidate final-test appendix metrics are produced before primary-source freeze.
- Main claim boundary: capacity-aware frontier is supported; unrestricted reject-option dominance is not.

## Debate Result

The reviewer accepted the rebuttal that final-test metrics were not used for source selection, but kept the locked-final-test objection partially unresolved. Weaknesses around unrestricted reject option, row-wise split wording, calibration-source claim narrowing, and Venn-Abers/empirical CRC overclaiming were accepted and are resolved only if manuscript wording follows the narrowed claims.
