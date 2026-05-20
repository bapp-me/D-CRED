# Advisor Review Experiment Code Review

**Date**: 2026-05-19

**Mode**: local-only checklist. Secondary-agent review was not used in this turn, so this file records the required `experiment-bridge` implementation checks locally.

## Reviewed Files

- `dcred/splits.py`
- `dcred/experiment.py`
- `dcred/cli.py`
- `scripts/economic_feature_acquisition_pilot.py`

## Checklist

| Check | Status | Notes |
|---|---|---|
| Hyperparameters exposed through CLI | PASS | `--role-split-mode`, `--selected-only-final-test`, and pilot utility parameters are exposed. |
| Random seed fixed and configurable | PASS | Existing `RunConfig.seed` remains in use; pilot has `--seed`. |
| Results saved as parseable CSV/JSON/Markdown | PASS | Month-blocked outputs and pilot outputs write CSV/JSON/MD artifacts. |
| Evaluation uses dataset ground truth | PASS | Decision and utility metrics compare against `Default`; no model output is used as truth. |
| Month-blocked split proves no shared month | PASS | `month_boundary_audit.csv` aggregates every issue month and records `n_roles`. |
| Selected-only final-test reporting | PASS | `--selected-only-final-test` writes one selected-source row to `calibration_final_appendix.csv` and updates `final_test_access_log.csv`. |
| True cash-flow fields handled honestly | PASS | Pilot checks current schema by construction and labels utility as proxy. No repayment cash-flow claim is made. |

## Non-Blocking Caveats

- Month-blocked small-sample runs can fail if `--lending-max-rows` covers fewer than seven issue months. This is expected and should be handled by using full data or a larger temporally representative subset.
- `scripts/economic_feature_acquisition_pilot.py` uses SGD models for a fast thesis-oriented pilot. It is not a tuned active feature acquisition method.
- The proxy utility pilot currently shows mixed evidence: uncertainty review slightly beats predicted VOI at the 5%, 10%, and 20% capacity points. This should remain a boundary result, not be rewritten as a method win.
- The true dean-level experiment needs a different data source with observed repayment cash-flow fields.

## Verification Commands

- `python -m compileall dcred scripts`
- `python -m dcred.cli run-reject-capacity --run-name reject_capacity_month_blocked --models lr lgbm xgb --rf-estimators 100 --xgb-estimators 300 --use-gpu-xgb --bootstrap 0 --role-split-mode month --selected-only-final-test --n-jobs 1`
- `python scripts\economic_feature_acquisition_pilot.py --run-name economic_feature_acquisition_pilot --role-split-mode month --review-cost 10 --seed 42`
