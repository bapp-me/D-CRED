# Blind Review Experiment Tracker

Updated: 20260520-234353
Output directory: `D:\code\diss_codex\D-CRED\outputs\blind_review_response_20260520-closure_safe`

| Run ID | Milestone | Purpose | Status | Notes |
|---|---|---|---|---|
| BR001 | M0 | Write frozen protocol | DONE | `locked_final_protocol/frozen_config.yaml` written. |
| BR002 | M0 | Record data and split hashes | DONE | `protocol_manifest.json` written. |
| BR003 | M0 | Define selected-only final output | DONE | Selected-only final probability and decision reports written. |
| BR004 | M0 | Reviewer coverage audit | DONE | `blind_review_coverage_matrix.csv` written. |
| BR101 | M1 | Build all-field audit table | DONE | `all_fields_feature_audit.csv` written. |
| BR102 | M1 | Define feature sets | DONE | `feature_set_definitions.csv` written. |
| BR103 | M1 | Define proxy/fairness groups | DONE | `responsible_credit_group_definitions.csv` written. |
| BR104 | M1 | Build with/without zip variants | DONE_CAPPED_SAME_MODEL | `zip_vs_nozip_policy_audit.csv` written. |
| BR201 | M2 | Locked primary rerun | DONE_TRUE_RERUN | Uses pre-run frozen rerun artifacts when `pre_run_freeze/` exists; otherwise retrospective wrapper. |
| BR202 | M2 | Locked references | DONE_SELECTED_ONLY | Selected-only final-test report retained from the active reject-run. |
| BR203 | M2 | D-CRED ablation A0 | DONE_LIMITED | `dcred_layer_ablation_table.csv` is a stitched evidence summary, not same-protocol proof. |
| BR204 | M2 | D-CRED same-protocol A1-A3 | DONE | `same_protocol_decision_ablation_table.csv` written for the selected final-test population. |
| BR205 | M2 | D-CRED ablation A4-A5 | DONE | Capacity and cash-flow objective summarized. |
| BR301 | M3 | Expected capacity frontier | DONE | `matched_capacity_frontier_with_ci.csv` written. |
| BR302 | M3 | Realized frontier CI | DONE | Issue-month bootstrap CI written. |
| BR303 | M3 | Matched baseline frontiers | DONE | Random, uncertainty, empirical-risk, and oracle rows are capacity-aligned. |
| BR304 | M3 | Oracle upper bound | DONE | Marked as unattainable. |
| BR305 | M3 | Monthly stability diagnostics | DONE_BOOTSTRAP | Issue-month bootstrap CI written; per-month appendix can still be expanded. |
| BR401 | M4 | Cost-sensitivity surface | DONE | `cost_sensitivity_surface.csv` written. |
| BR402 | M4 | Break-even table | DONE | `break_even_table.csv` written. |
| BR403 | M4 | Near-all-review region map | DONE | `near_all_review_region_map.csv` written. |
| BR404 | M4 | Sensitivity appendix export | DONE | Full grid CSV written. |
| BR501 | M5 | Cash-flow frontier data | DONE | Approval-constrained cash-flow frontier copied from clean full rerun. |
| BR502 | M5 | Cash-flow frontier CI | DONE | Month bootstrap CI written. |
| BR503 | M5 | Coverage-constrained best policy | DONE | Deployable best-policy table written. |
| BR504 | M5 | Cash model weakness report | DONE_REUSED | `model_metrics.csv` copied when available. |
| BR601 | M6 | Subgroup decision audit | DONE | `responsible_credit_audit.csv` written. |
| BR602 | M6 | Subgroup calibration audit | DONE | `subgroup_calibration_bins.csv` written. |
| BR603 | M6 | With-vs-without zip audit | DONE_CAPPED_SAME_MODEL | `zip_vs_nozip_policy_audit.csv` isolates zip-code proxy effect. |
| BR604 | M6 | Strict/default/expanded model stress | DONE_CAPPED_SAME_MODEL | LGBM/sigmoid feature stress written with `50000` row cap. |
| BR605 | M6 | Responsible-credit disclaimer | DONE | Claim-control summary states no compliance claim. |
| BR701 | M7 | Result-to-claim update | DONE_DRAFT | Blind-review claim-control summary written. |
| BR702 | M7 | Thesis table map | PARTIAL | Generated file list in result summary; thesis source not edited here. |
| BR703 | M7 | Handoff update | PENDING | Do after reviewing outputs and claim boundaries. |
| BR704 | M7 | Final claim audit | PENDING | Requires thesis text after integration. |
