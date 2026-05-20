# Blind Review Experiment Tracker

Updated: 2026-05-20 22:00

Primary plan: `refine-logs/BLIND_REVIEW_EXPERIMENT_PLAN.md`

Scope: Convert every actionable point in `../专家盲审.md` into executable D-CRED reviewer-response experiments. Initial status is `TODO`; no new experimental result is claimed here.

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| BR001 | M0 | Write frozen protocol | `locked_final_protocol/frozen_config.yaml` | month-blocked roles | config fields, config hash | MUST | TODO | Must freeze dataset, feature list, model list, calibrator list, selection rule, cost grid, capacity grid, bootstrap plan before final_test report. |
| BR002 | M0 | Record data and split hashes | protocol manifest | all roles | data hash, split counts, month audit | MUST | TODO | Include no-shared-month audit and mark old all-candidate final-test tables as post-hoc diagnostics. |
| BR003 | M0 | Define selected-only final output | primary source + pre-registered references | final_test | selected-only probability and decision metrics | MUST | TODO | Do not output a new all-candidate final-test leaderboard as main evidence. |
| BR004 | M0 | Reviewer coverage audit | blind review coverage matrix | n/a | covered expert points | MUST | TODO | Preserve expert numbering: 1, 2, 3, 4, 6, 8, 11. |
| BR101 | M1 | Build all-field audit table | full raw Lending fields | n/a | category, allowed flag, reason | MUST | TODO | Categories: application-time, policy-generated, post-origination, repayment outcome, administrative, text, timestamp, uncertain. |
| BR102 | M1 | Define feature sets | strict/default/expanded | locked roles | field counts, rationale | MUST | TODO | Expanded is a stress test only, not clean deployment evidence. |
| BR103 | M1 | Define proxy/fairness groups | addr_state, zip3/state cluster, home_ownership, income decile, loan_amnt decile, purpose | final_test | group sizes, suppression flags | MUST | TODO | No legal compliance claim; this is risk exposure only. |
| BR104 | M1 | Build with/without zip variants | default features vs no zip/proxy | locked roles | model and decision deltas | MUST | TODO | Addresses proxy-effect concern around state/zip variables. |
| BR201 | M2 | Locked primary rerun | selected calibrated source | month-blocked final_test | Brier, ECE, NLL, AUC, PR-AUC | MUST | TODO | Expected primary source is selected by frozen calibration_select rule; do not select on final_test. |
| BR202 | M2 | Locked references | LR/sigmoid, XGB/sigmoid if pre-registered | month-blocked final_test | probability and policy metrics | SHOULD | TODO | Keep reference list short and pre-registered. |
| BR203 | M2 | D-CRED ablation A0 | random split + AUC only | random test | AUC, PR-AUC, ranking | MUST | TODO | Shows traditional conclusion. |
| BR204 | M2 | D-CRED ablation A1-A3 | temporal, calibration, cost threshold | locked roles | calibration, expected/realized cost, approval rate | MUST | TODO | Isolates temporal, calibration, and cost-sensitive threshold layers. |
| BR205 | M2 | D-CRED ablation A4-A5 | capacity review and cash-flow objective | final_test | review frontier, net_cash frontier | MUST | TODO | Links capacity-aware and cash-flow layers into the main contribution table. |
| BR301 | M3 | Expected capacity frontier | D-CRED benefit rank | final_test | expected cost by capacity | MUST | TODO | Label monotonic expected frontier as optimization property. |
| BR302 | M3 | Realized frontier CI | D-CRED benefit rank | final_test | realized cost, savings, 95% CI | MUST | TODO | Prefer issue-month block bootstrap; report observation bootstrap only with caveat. |
| BR303 | M3 | Matched baseline frontiers | random, uncertainty-band, split conformal, empirical conformal | final_test | cost, review rate, CI | MUST | TODO | Plot on same figure as capacity-aware deferral. |
| BR304 | M3 | Oracle upper bound | realized benefit oracle | final_test | unattainable best frontier | SHOULD | TODO | Clearly mark as upper bound, not deployable policy. |
| BR305 | M3 | Monthly stability diagnostics | per-month frontier summaries | final_test months | rank stability, cost variance | SHOULD | TODO | Supports or limits cross-month stability claim. |
| BR401 | M4 | Cost-sensitivity surface | FN:FP x review cost x rho x capacity | final_test | expected/realized cost, winner map | MUST | TODO | Grid: 2/5/10/20; review cost 0.01-1.0; rho 0-0.5; capacity 1/5/10/20/50%. |
| BR402 | M4 | Break-even table | case-level review condition | final_test | share review-beneficial by scenario | MUST | TODO | Use `c_R < (1-rho) * min(C_A, C_D)`. |
| BR403 | M4 | Near-all-review region map | unrestricted reject option | final_test | review rate >80/90/95% | MUST | TODO | Explains why 99.1% review is a cost-regime artifact. |
| BR404 | M4 | Sensitivity appendix export | full grid CSV/heatmap | final_test | full surface tables | MUST | TODO | Main paper should show summarized surfaces; appendix stores full grid. |
| BR501 | M5 | Cash-flow frontier data | PD ranking, cash ranking, hybrid, random | dean final_test | approval grid metrics | MUST | TODO | Approval rates: 1/5/10/20/30/50/65%. |
| BR502 | M5 | Cash-flow frontier CI | same policies | dean final_test months | mean/total net_cash CI, default-rate CI | MUST | TODO | Prevent single-threshold low-approval result from carrying the section. |
| BR503 | M5 | Coverage-constrained best policy | best policy per approval rate | dean final_test | mean net_cash, default rate | MUST | TODO | The 0.74% tuned cash result becomes one frontier point, not the headline win. |
| BR504 | M5 | Cash model weakness report | cheap/full cash models | dean final_test | MAE, R2, low-approval caveat | MUST | TODO | If R2 remains negative, say so in the main text. |
| BR601 | M6 | Subgroup decision audit | primary locked policy and no-review baseline | final_test | approval, rejection, review, default | MUST | TODO | Group by state/zip cluster/home ownership/income decile/loan amount decile/purpose. |
| BR602 | M6 | Subgroup calibration audit | primary source | final_test | Brier, ECE, reliability bins | MUST | TODO | Generate subgroup calibration plots where group sizes are adequate. |
| BR603 | M6 | With-vs-without zip audit | proxy feature variants | locked final_test | subgroup and overall deltas | MUST | TODO | Directly addresses geography/proxy concern. |
| BR604 | M6 | Strict/default/expanded model stress | three feature protocols | locked roles | AUC, Brier, ECE, cost, review rate | MUST | TODO | Expanded performance gains must be interpreted as leakage/proxy risk. |
| BR605 | M6 | Responsible-credit disclaimer | audit prose | n/a | claim wording | MUST | TODO | State clearly: not a legal compliance certification. |
| BR701 | M7 | Result-to-claim update | blind-review claim-control file | all outputs | supported/unsupported claims | MUST | TODO | Write after experiments; do not update claims before results exist. |
| BR702 | M7 | Thesis table map | table/figure source map | all outputs | source files for every number | MUST | TODO | Prevent stale handoff numbers from entering final dissertation. |
| BR703 | M7 | Handoff update | paper_writing_handoff README and narrative pointers | n/a | priority file list | SHOULD | TODO | Only after outputs exist and claim-control is updated. |
| BR704 | M7 | Final claim audit | dissertation text vs CSV/JSON | thesis draft | numeric consistency | MUST | TODO | Required before telling a future model the thesis is finished. |
