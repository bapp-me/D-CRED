# D-CRED Output Manifest

| Timestamp | Skill | File | Stage | Description |
|---|---|---|---|---|
| 2026-05-04 00:44 | /auto-review-loop | review-stage/AUTO_REVIEW.md | review | cumulative D-CRED auto-review log |
| 2026-05-04 00:44 | /auto-review-loop | review-stage/REVIEW_STATE.json | review | auto-review loop state |
| 2026-05-04 00:58 | /auto-review-loop | outputs/review_round1_fix/ | experiment | Lending-only rerun with corrected selective review-cost basis and decision delta CIs |
| 2026-05-04 00:58 | /auto-review-loop | review-stage/ROUND1_FIX_SUMMARY.md | review | claim-control and result summary after Round 1 fixes |
| 2026-05-04 00:58 | /auto-review-loop | review-stage/lending_decision_delta_ci.csv | review | paired bootstrap expected-cost deltas for key Lending decisions |
| 2026-05-04 00:58 | /auto-review-loop | review-stage/reduced_calibration_summary.csv | review | reduced-protocol calibration mean/std summary |
| 2026-05-04 00:58 | /auto-review-loop | review-stage/reduced_cost_summary.csv | review | reduced-protocol cost-policy mean/std summary |
| 2026-05-04 00:58 | /auto-review-loop | review-stage/reduced_selective_summary.csv | review | reduced-protocol selective-decision summary |
| 2026-05-04 00:59 | /auto-review-loop | review-stage/TRACE_ROUND1.md | review | reviewer route and action trace |
| 2026-05-04 01:08 | /auto-review-loop | review-stage/TRACE_ROUND2.md | review | reviewer re-review route and stop decision |
| 2026-05-04 01:08 | /auto-review-loop | review-stage/AUTO_REVIEW_20260504_010800.md | review | timestamped D-CRED auto-review log |
| 2026-05-04 01:08 | /result-to-claim | CLAIMS_FROM_RESULTS.md | claim-control | supported and unsupported D-CRED claims after review |
| 2026-05-04 01:08 | /result-to-claim | CLAIMS_FROM_RESULTS_20260504_010800.md | claim-control | timestamped D-CRED claim summary |
| 2026-05-04 01:08 | /result-to-claim | findings.md | claim-control | D-CRED findings and limitations for dissertation writing |
| 2026-05-18 21:45 | /experiment-plan | refine-logs/TEACHER_REVIEW_EXPERIMENT_PLAN_20260518_214547.md | implementation | timestamped P0/P1 supervisor-review reinforcement experiment plan |
| 2026-05-18 21:45 | /experiment-plan | refine-logs/TEACHER_REVIEW_EXPERIMENT_PLAN.md | implementation | latest P0/P1 supervisor-review reinforcement experiment plan |
| 2026-05-18 21:45 | /experiment-plan | refine-logs/TEACHER_REVIEW_EXPERIMENT_TRACKER_20260518_214547.md | implementation | timestamped run tracker for P0/P1 supervisor-review reinforcement work |
| 2026-05-18 21:45 | /experiment-plan | refine-logs/TEACHER_REVIEW_EXPERIMENT_TRACKER.md | implementation | latest run tracker for P0/P1 supervisor-review reinforcement work |
| 2026-05-18 22:07 | /experiment-bridge | outputs/teacher_review_p1_20260518_220742 | teacher-review-p1 | timestamped P0/P1 supervisor-review reinforcement analysis outputs |
| 2026-05-18 22:07 | /experiment-bridge | outputs/teacher_review_p1_latest | teacher-review-p1 | latest fixed-name P0/P1 reinforcement analysis outputs |
| 2026-05-18 22:07 | /experiment-bridge | refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md | teacher-review-p1 | latest P0/P1 experiment result summary |
| 2026-05-18 23:10 | /auto-review-loop | CLAIMS_FROM_RESULTS.md | claim-control | updated teacher-review P0/P1 claim boundaries and all-review caveat |
| 2026-05-18 23:10 | /auto-review-loop | outputs/teacher_review_p1_latest/all_review_residual_error_reference.csv | teacher-review-p1 | all-review residual-error reference for selective-decisioning caveat |
| 2026-05-18 23:10 | /auto-review-loop | review-stage/REVIEWER_MEMORY.md | review | hard-mode reviewer memory for teacher-review P0/P1 supplement |
| 2026-05-18 23:10 | /auto-review-loop | review-stage/TRACE_TEACHER_P1_ROUND1.md | review | hard-mode teacher-review P0/P1 review trace |
| 2026-05-18 23:10 | /auto-review-loop | refine-logs/TEACHER_REVIEW_SOURCE_SPECIFIC_CLAIM_AUDIT.md | claim-control | source-specific audit after teacher-review P0/P1 hard-review fixes |
| 2026-05-18 23:10 | /auto-review-loop | ../ntu-dissertation/latex/ | dissertation-writing | narrowed deployment-oriented and all-review caveat wording in dissertation source |
| 2026-05-18 23:10 | /auto-review-loop | review-stage/TRACE_TEACHER_P1_ROUND2.md | review | hard-mode teacher-review P0/P1 re-review trace and ready verdict |
| 2026-05-18 23:10 | /auto-review-loop | review-stage/REVIEW_STATE.json | review | completed hard-mode teacher-review P0/P1 loop state |
| 2026-05-19 00:32 | /experiment-plan | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_PLAN_20260519_003218.md | implementation | timestamped full-data reject-option and capacity-aware D-CRED experiment plan |
| 2026-05-19 00:32 | /experiment-plan | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_PLAN.md | implementation | latest full-data reject-option and capacity-aware D-CRED experiment plan |
| 2026-05-19 00:32 | /experiment-plan | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_TRACKER_20260519_003218.md | implementation | timestamped tracker for reject-option and capacity-aware D-CRED rerun |
| 2026-05-19 00:32 | /experiment-plan | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_TRACKER.md | implementation | latest tracker for reject-option and capacity-aware D-CRED rerun |
| 2026-05-19 00:54 | /experiment-bridge | outputs/reject_capacity_sanity | reject-capacity | sanity-stage 10k-row role-split reject-option/capacity run |
| 2026-05-19 00:54 | /experiment-bridge | outputs/reject_capacity_lr_full | reject-capacity | full-row no-cap LR role-split reject-option/capacity run |
| 2026-05-19 00:54 | /experiment-bridge | outputs/reject_capacity_lgbm_full | reject-capacity | full-row no-cap LightGBM role-split reject-option/capacity run |
| 2026-05-19 00:54 | /experiment-bridge | outputs/reject_capacity_xgb_full | reject-capacity | full-row no-cap XGBoost CUDA role-split reject-option/capacity run |
| 2026-05-19 00:54 | /experiment-bridge | outputs/reject_capacity_full | reject-capacity | combined full-row no-cap LR/LightGBM/XGBoost run with calibration-select primary source and capacity frontier |
| 2026-05-19 00:57 | /experiment-bridge | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_RESULTS_20260519_005742.md | reject-capacity | timestamped result summary for combined full-row reject-option/capacity run |
| 2026-05-19 00:57 | /experiment-bridge | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_RESULTS.md | reject-capacity | latest result summary for combined full-row reject-option/capacity run |
| 2026-05-19 00:57 | /experiment-bridge | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_TRACKER_20260519_005742.md | reject-capacity | timestamped tracker after combined full-row reject-option/capacity run |
| 2026-05-19 00:57 | /experiment-bridge | refine-logs/REJECT_OPTION_CAPACITY_EXPERIMENT_TRACKER.md | reject-capacity | latest tracker after combined full-row reject-option/capacity run |
| 2026-05-19 00:57 | /experiment-bridge | refine-logs/EXPERIMENT_CODE_REVIEW.md | code-review | local-only checklist for role-split reject-option/capacity implementation |
| 2026-05-19 22:15 | /experiment-plan | refine-logs/ADVISOR_REVIEW_EXPERIMENT_PLAN_20260519_221538.md | implementation | timestamped plan from supervisor/dean review advice |
| 2026-05-19 22:15 | /experiment-plan | refine-logs/ADVISOR_REVIEW_EXPERIMENT_PLAN.md | implementation | latest plan from supervisor/dean review advice |
| 2026-05-19 22:15 | /experiment-plan | refine-logs/ADVISOR_REVIEW_EXPERIMENT_TRACKER_20260519_221538.md | implementation | timestamped tracker for advisor review experiments |
| 2026-05-19 22:15 | /experiment-plan | refine-logs/ADVISOR_REVIEW_EXPERIMENT_TRACKER.md | implementation | latest tracker for advisor review experiments |
| 2026-05-19 22:19 | /experiment-bridge | outputs/reject_capacity_month_blocked | implementation | full month-blocked selected-only-final reject-capacity rerun |
| 2026-05-19 22:13 | /experiment-bridge | outputs/economic_feature_acquisition_pilot | implementation | proxy utility and two-stage feature-acquisition pilot |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON_20260519_221538.csv | implementation | timestamped row-wise versus month-blocked capacity-frontier comparison |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_ROW_VS_MONTH_COMPARISON.csv | implementation | latest row-wise versus month-blocked capacity-frontier comparison |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_EXPERIMENT_RESULTS_20260519_221538.md | implementation | timestamped advisor review experiment result summary |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_EXPERIMENT_RESULTS.md | implementation | latest advisor review experiment result summary |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_EXPERIMENT_CODE_REVIEW_20260519_221538.md | code-review | timestamped local-only code review for advisor experiments |
| 2026-05-19 22:15 | /experiment-bridge | refine-logs/ADVISOR_REVIEW_EXPERIMENT_CODE_REVIEW.md | code-review | latest local-only code review for advisor experiments |
| 2026-05-19 23:16 | /experiment-plan | refine-logs/DEAN_CASHFLOW_EXPERIMENT_PLAN_20260519_231627.md | dean-cashflow | timestamped observed-cash-flow experiment plan from dean review |
| 2026-05-19 23:16 | /experiment-plan | refine-logs/DEAN_CASHFLOW_EXPERIMENT_PLAN.md | dean-cashflow | latest observed-cash-flow experiment plan from dean review |
| 2026-05-19 23:16 | /experiment-plan | refine-logs/DEAN_CASHFLOW_EXPERIMENT_TRACKER_20260519_231627.md | dean-cashflow | timestamped tracker for dean cash-flow experiments |
| 2026-05-19 23:16 | /experiment-plan | refine-logs/DEAN_CASHFLOW_EXPERIMENT_TRACKER.md | dean-cashflow | latest tracker for dean cash-flow experiments |
| 2026-05-19 23:40 | /experiment-bridge | scripts/cashflow_feature_acquisition_experiment.py | dean-cashflow | observed Lending Club cash-flow and feature-acquisition experiment implementation |
| 2026-05-19 23:40 | /experiment-bridge | outputs/dean_cashflow_full/ | dean-cashflow | full Lending Club cash-flow experiment outputs and CSV result tables |
| 2026-05-19 23:40 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS_20260519_234000.md | dean-cashflow | timestamped result summary for full observed-cash-flow experiment |
| 2026-05-19 23:40 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md | dean-cashflow | latest result summary for full observed-cash-flow experiment |
| 2026-05-19 23:40 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_CODE_REVIEW_20260519_234000.md | code-review | timestamped local code review for dean cash-flow implementation |
| 2026-05-19 23:40 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_CODE_REVIEW.md | code-review | latest local code review for dean cash-flow implementation |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/AUTO_REVIEW_20260520_REVIEWER_RESPONSE_NIGHTMARE.md | review | timestamped nightmare review of advisor month-blocked and dean cash-flow reviewer-response experiments |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_BEAUVOIR_20260520.md | review | raw primary reviewer response for reviewer-response nightmare audit |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_ROUND1_ERDOS_20260520.md | review | raw fresh adversarial verifier response for reviewer-response nightmare audit |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_DEBATE_20260520.md | review | raw debate ruling for reviewer-response nightmare audit |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/TRACE_REVIEWER_RESPONSE_NIGHTMARE_20260520.md | review | trace for nightmare reviewer-response audit |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/REVIEWER_MEMORY.md | review | updated reviewer memory with reviewer-response claim boundaries |
| 2026-05-20 00:16 | /auto-review-loop | review-stage/REVIEW_STATE.json | review | completed state for reviewer-response nightmare audit |
| 2026-05-20 00:25 | /experiment-bridge | scripts/cashflow_feature_acquisition_experiment.py | dean-cashflow | removed `funded_amnt` from predictors and added resolver guardrail excluding cash-flow columns |
| 2026-05-20 00:25 | /experiment-bridge | outputs/dean_cashflow_full/ | dean-cashflow | clean dean cash-flow rerun after `funded_amnt` predictor fix |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS_20260520_002513.md | dean-cashflow | timestamped clean cash-flow rerun result summary |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_RESULTS.md | dean-cashflow | latest clean cash-flow rerun result summary |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_CODE_REVIEW_20260520_002513.md | code-review | timestamped code review for `funded_amnt` predictor repair |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_CODE_REVIEW.md | code-review | latest code review for clean dean cash-flow rerun |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_TRACKER_20260520_002513.md | dean-cashflow | timestamped tracker for clean cash-flow rerun |
| 2026-05-20 00:25 | /experiment-bridge | refine-logs/DEAN_CASHFLOW_EXPERIMENT_TRACKER.md | dean-cashflow | latest tracker for clean dean cash-flow rerun |
| 2026-05-20 00:25 | /experiment-bridge | ../paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260519.md | writing-handoff | updated dean writing handoff with clean rerun numbers and claim boundaries |
| 2026-05-20 00:25 | /experiment-bridge | ../paper_writing_handoff_20260511/03_narrative_and_plan/ADVISOR_REVIEW_WRITING_UPDATE_20260519.md | writing-handoff | marked proxy-only dean pilot as superseded by full cash-flow rerun |
| 2026-05-20 00:25 | /experiment-bridge | ../paper_writing_handoff_20260511/03_narrative_and_plan/DEAN_CASHFLOW_WRITING_UPDATE_20260520.md | writing-handoff | timestamped dean writing update for clean cash-flow rerun |
| 2026-05-20 00:25 | /experiment-bridge | ../paper_writing_handoff_20260511/03_narrative_and_plan/ADVISOR_REVIEW_WRITING_UPDATE_20260520.md | writing-handoff | timestamped advisor writing update marking dean proxy pilot superseded |
| 2026-05-20 00:25 | /experiment-bridge | review-stage/AUTO_REVIEW.md | review | appended dean cash-flow repair follow-up after clean rerun |
| 2026-05-20 22:00 | /experiment-plan | refine-logs/BLIND_REVIEW_EXPERIMENT_PLAN_20260520_220049.md | blind-review | timestamped experiment plan converting every blind-review expert point into claim-driven D-CRED reviewer-response experiments |
| 2026-05-20 22:00 | /experiment-plan | refine-logs/BLIND_REVIEW_EXPERIMENT_PLAN.md | blind-review | latest blind-review experiment plan |
| 2026-05-20 22:00 | /experiment-plan | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER_20260520_220049.md | blind-review | timestamped tracker for blind-review experiment plan |
| 2026-05-20 22:00 | /experiment-plan | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER.md | blind-review | latest tracker for blind-review experiment plan |

| 2026-05-20 22:31 | /experiment-bridge | outputs/blind_review_response_20260520-223108 | blind-review | timestamped blind-review reviewer-response evidence pack |
| 2026-05-20 22:31 | /experiment-bridge | outputs/blind_review_response_latest | blind-review | latest blind-review reviewer-response evidence pack |
| 2026-05-20 22:31 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_RESULTS.md | blind-review | latest blind-review experiment result summary |
| 2026-05-20 22:31 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_CODE_REVIEW.md | code-review | local-only code review for blind-review response implementation |
| 2026-05-20 22:31 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER.md | blind-review | tracker updated after blind-review response experiment run |

| 2026-05-20 22:33 | /experiment-bridge | outputs/blind_review_response_20260520-223244 | blind-review | timestamped blind-review reviewer-response evidence pack |
| 2026-05-20 22:33 | /experiment-bridge | outputs/blind_review_response_latest | blind-review | latest blind-review reviewer-response evidence pack |
| 2026-05-20 22:33 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_RESULTS.md | blind-review | latest blind-review experiment result summary |
| 2026-05-20 22:33 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_CODE_REVIEW.md | code-review | local-only code review for blind-review response implementation |
| 2026-05-20 22:33 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER.md | blind-review | tracker updated after blind-review response experiment run |

| 2026-05-20 22:34 | /experiment-bridge | outputs/blind_review_response_20260520-223406 | blind-review | timestamped blind-review reviewer-response evidence pack |
| 2026-05-20 22:34 | /experiment-bridge | outputs/blind_review_response_latest | blind-review | latest blind-review reviewer-response evidence pack |
| 2026-05-20 22:34 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_RESULTS.md | blind-review | latest blind-review experiment result summary |
| 2026-05-20 22:34 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_CODE_REVIEW.md | code-review | local-only code review for blind-review response implementation |
| 2026-05-20 22:34 | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER.md | blind-review | tracker updated after blind-review response experiment run |

| 2026-05-20 23:20 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_ROUND1_CONFUCIUS_20260520.md | review | raw primary nightmare review for blind-review response package |
| 2026-05-20 23:20 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_ROUND1_KANT_20260520.md | review | raw fresh adversarial verification for blind-review response package |
| 2026-05-20 23:20 | /auto-review-loop | review-stage/RAW_REVIEWER_RESPONSE_NIGHTMARE_BLIND_DEBATE_20260520.md | review | debate ruling for blind-review response package |
| 2026-05-20 23:20 | /auto-review-loop | review-stage/TRACE_BLIND_REVIEW_NIGHTMARE_20260520.md | review | trace for blind-review nightmare audit |
| 2026-05-20 23:20 | /auto-review-loop | review-stage/CLAIMS_FROM_RESULTS_BLIND_REVIEW_NIGHTMARE_20260520.md | claim-control | downgraded claim boundary after blind-review nightmare audit |
| 2026-05-20 23:20 | /auto-review-loop | review-stage/REVIEW_STATE.json | review | completed blind-review nightmare audit state |
