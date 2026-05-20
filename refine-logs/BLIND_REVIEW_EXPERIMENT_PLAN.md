# Blind Review Experiment Plan

**Problem**: 当前 D-CRED 硕士论文已经可以支撑收窄后的 MSc defense 叙事，但盲审专家指出它仍像一份多轮防守后的技术报告。下一轮实验必须把论文改成一个 claim-driven 的证据链：证明传统信用风险 benchmark 在特征时点、时间隔离、校准、成本、复核容量、现金流目标、责任信用和字段控制这些层面会改变结论。

**Method Thesis**: D-CRED 不应再被表述为一个新算法，而应被表述为一个部署导向的信用风险决策评估框架；其贡献是系统证明每一层部署假设如何改变模型选择、阈值选择、复核分配和经济解释边界。

**Date**: 2026-05-20

**Primary review source**: `专家盲审.md`

**Current evidence boundary**: 以 `paper_writing_handoff_20260511/` 为入口；当前主证据为 `reject_capacity_month_blocked/` 的 strict temporal robustness、`dean_cashflow_full/` 的 observed cash-flow decisioning、以及 `reject_capacity_full/` 的 continuity capacity-frontier evidence。旧 `full/` 和 `review_round1_fix/` 只能作为历史支持，不能作为新主 claim 的主证据。

## Blind Review Coverage Matrix

原盲审文件编号跳过了 5、7、9、10。本规划保留专家原编号，并覆盖所有实际出现的意见点。

| Expert Point | Core Critique | Current Status | Required Plan Block | Main Output |
|---|---|---|---|---|
| 1. 贡献太防守 | D-CRED 不是新算法、理论、formal conformal guarantee 或生产系统；必须证明每一层 pipeline 都会改变解释边界。 | 当前论文已有框架叙事，但缺少一个总 ablation table 把各层串成贡献证据。 | B1 | `dcred_layer_ablation_table.csv` 和论文主表：random/AUC only -> temporal -> calibration -> cost -> capacity -> cash-flow。 |
| 2. final-test 不够干净 | 旧 run 在 primary-source freeze 前生成过 all-candidate final-test appendix metrics；不能声称 pristine locked final test。 | `reject_capacity_month_blocked` 已有 selected-only final 支持，但仍需要按盲审要求明确生成一个命名为 `locked_final_protocol` 的完整冻结复现实验包。 | B0, B2 | `frozen_config.yaml`、配置 hash、selected-only final-test report、post-hoc diagnostics 标注。 |
| 3. capacity frontier 单调性可能是数学构造 | 按 review benefit 排序天然会让 expected cost 随容量不升；不能把单调下降包装成发现。 | 当前已有 expected frontier 和若干 baselines，但缺少同图 baseline frontier、realized-cost CI、month/block bootstrap。 | B3 | expected frontier + realized frontier with CI + random/uncertainty/conformal/oracle baseline frontier。 |
| 4. 成本和人工复核假设任意 | FN:FP、review cost、human residual 都是 stylized assumptions；near all-review 说明主 scenario 对 review 太友好。 | 已有部分 sensitivity，但缺少完整 FN:FP x review cost x rho x capacity surface 和 break-even derivation。 | B4 | cost-sensitivity surface、break-even condition、near all-review region map。 |
| 6. cash-flow 结果危险 | tuned cash model 靠极低 approval rate 获胜，cash R2 仍为负；不能和正常批准率策略直接比较。 | `dean_cashflow_full` 已承认低批准率和弱 cash regression，但需要 approval-constrained frontier。 | B5 | utility-approval frontier：固定 approval rates 下比较 PD/cash/hybrid/random。 |
| 8. Responsible AI / 合规边界不足 | deployment-oriented 论文不能只谈 AUC、Brier 和 cost frontier；需要 subgroup calibration、disparate-impact 风险暴露和 zip/proxy audit。 | 当前明确“不支持 fairness compliance”，但没有最低限度 responsible-credit audit。 | B6 | subgroup table、subgroup calibration plots、with/without zip-code comparison、合规免责声明。 |
| 11. feature audit 太粗 | 只列少量字段不足以证明 application-time protocol；需要全字段清单和 contaminated-feature stress test。 | 当前 P0 audit 是关键词筛查，不是全量字段审计。 | B7 | all-field feature audit appendix、strict/default/expanded feature-set comparison。 |

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: D-CRED 的贡献是分层暴露部署假设如何改变信用风险决策，而不是提出新分类器。 | 回应“贡献太防守”的主审质询。 | 一个完整 ablation table 显示每一层是否改变 model ranking、calibration quality、threshold、approval/review rate、expected/realized cost 或 cash utility。 | B1 |
| C2: 新证据包可以消除“看过 final_test 后再选叙事”的主要嫌疑。 | 这是答辩可信度的底线。 | `locked_final_protocol` 在运行前冻结 config，只输出 selected primary source 和少量预注册 baselines；旧 all-candidate final-test 指标全部标为 post-hoc diagnostics。 | B0, B2 |
| C3: capacity frontier 的有效 claim 是 comparative realized-cost trade-off，不是单调性本身。 | 避免被统计评审击穿。 | expected frontier 明确作为模型内优化；realized frontier 给 block/month bootstrap CI；同一图表比较 random、uncertainty、conformal、oracle upper bound。 | B3 |
| C4: review value 只在明确成本、人类残差和容量区域内成立。 | 回应成本假设和 near all-review 质疑。 | FN:FP、review cost、rho、capacity 四维 sensitivity surface；给出 break-even 条件并标出 all-review/reject-option 饱和区域。 | B4 |
| C5: cash-flow 结论必须是 utility-approval frontier，而不是单点最优阈值。 | 避免“几乎不放款所以赢”的质疑。 | 在固定 approval rate 下比较 PD ranking、predicted cash ranking、hybrid ranking 和 random；报告 mean/total net_cash、default rate、CI 和 coverage-constrained best policy。 | B5 |
| C6: D-CRED 的部署导向必须包含 responsible-credit risk exposure 和字段控制证据。 | 把“不是法律合规认证”与“最低限度风险暴露”区分开。 | subgroup calibration/decision table、zip/proxy ablation、strict/default/expanded feature sets、全字段 allow/ban rationale。 | B6, B7 |

## Paper Storyline

Main paper must prove:

- D-CRED 是部署假设分层评估框架，不是新算法。
- 各层实验可以解释传统 random split + AUC 评价为什么不足。
- final-test 新证据包是冻结协议下的 selected-only report；旧全候选 final-test 表只作为 post-hoc appendix。
- capacity result 的重点是相对复核分配策略和 realized-cost uncertainty，不是“容量越大成本越低”这个机械事实。
- 人工复核经济性有明确 break-even region；near all-review 是成本假设的结果，不是可部署策略。
- cash-flow 只支持 accepted/funded-loan policy evaluation；现金流模型弱、低批准率和 missed-profitable-loan opportunity cost 必须正面写。
- responsible-credit audit 只做部署前风险暴露，不声称法律合规认证或 reject inference。
- feature audit 从“小表”升级为全字段 protocol 和 strict/default/expanded stress test。

Appendix can support:

- 全量字段清单和字段分类理由。
- 额外 bootstrap CI、每月稳定性、每州/zip3/state-cluster subgroup 图。
- UCI/German reduced-protocol sanity checks。
- 旧 `reject_capacity_full` 与 `review_round1_fix` 的历史 continuity tables。

Experiments intentionally cut:

- 新模型 SOTA 竞赛。
- formal Venn-Abers / conformal finite-sample guarantee claim。
- production-bank ROI、real human reviewer correctness、legal compliance certification。
- rejected-applicant full-population reject inference，除非后续单独立项。

## Experiment Blocks

### Block 0: Protocol Freeze And Evidence Hygiene

- **Claim tested**: 新实验包是否能消除 final-test 污染和叙事后验选择的主要嫌疑。
- **Why this block exists**: 专家第 2 点明确要求 `locked_final_protocol`，并要求 final_test 前固定 dataset、feature list、split、model list、calibrator list、selection rule、cost grid 和 primary metric。
- **Dataset / split / task**: Lending Club primary dataset；优先使用 strict month-blocked seven-role split；若同时保留 row-wise continuity split，必须标为 secondary robustness。
- **Compared systems**: 预注册 primary source selection rule 选出的 `lgbm/sigmoid`；少量预注册 baselines 如 LR/sigmoid、XGB/sigmoid、no-review/all-review references。禁止生成新的 all-candidate final-test ranking 作为主证据。
- **Metrics**: config hash、data hash、split audit、selected-source final-test Brier/ECE/NLL/AUC/PR-AUC、final decision metrics、capacity metrics。
- **Setup details**:
  - 先写 `outputs/locked_final_protocol/frozen_config.yaml`。
  - 固定 feature sets、model/calibrator candidates、selection metric、capacity grid、cost grid、bootstrap plan。
  - final-test selected-only report 与 post-hoc diagnostics 分文件输出。
  - 旧 all-candidate final-test appendix metrics 在论文中统一标注为 post-hoc diagnostics。
- **Success criterion**: 新结果即使数值不提升，也能说“原版本不够干净；locked rerun 结论方向稳定/不稳定如下”。
- **Failure interpretation**: 若 locked rerun 改变结论，论文必须以 locked rerun 为准，旧结果降级为历史。
- **Table / figure target**: 第 4 章 protocol table，第 5 章 locked-final main result table，附录 post-hoc diagnostic table。
- **Priority**: MUST-RUN.

### Block 1: D-CRED Layer Ablation Table

- **Claim tested**: D-CRED 的贡献是否来自系统改变评价对象，而非“把已有技术堆在 pipeline 里”。
- **Why this block exists**: 专家第 1 点要求证明每一层必要，或至少证明每一层改变解释边界。
- **Dataset / split / task**: Lending Club locked protocol；主表使用 month-blocked final_test；必要时用旧 row-wise结果作 continuity appendix。
- **Compared systems**:
  - A0 `random split + AUC only`: 去掉 temporal、calibration、cost、review 和 cash-flow。
  - A1 `temporal split only`: 加时间，不加 calibration。
  - A2 `temporal + calibration`: raw/sigmoid/isotonic 概率质量比较。
  - A3 `+ cost-sensitive threshold`: 固定 0.5、F1 threshold、cost threshold。
  - A4 `+ capacity-aware review`: no-review、all-review、capacity-aware deferral、uncertainty/conformal baselines。
  - A5 `+ cash-flow objective`: PD threshold、predicted cash ranking、hybrid ranking、approval-constrained policy。
- **Metrics**:
  - Decisive: ranking change, Brier/ECE/NLL, expected and realized cost, review rate, approval rate, mean/total net_cash。
  - Secondary: AUC/PR-AUC, default-rate shift, calibration plot, automation rate。
- **Setup details**:
  - 每一层只增加一个部署假设，避免一次性比较无法归因。
  - 每行保留“解释边界变化”列：changed / unchanged / negative。
  - 若某层不提升性能，写成“改变解释边界”而不是硬凹 wins。
- **Success criterion**: 至少能清楚说明哪些层改变主结论，哪些层只是限制 claim。
- **Failure interpretation**: 若某些层影响弱，论文改写为“不是每层都提升，但每层界定了何种结论不能写”。
- **Table / figure target**: 论文最重要主表 `D-CRED Ablation Table`。
- **Priority**: MUST-RUN.

### Block 2: Locked Final Protocol Rerun

- **Claim tested**: 当前最强 revised result 是否在完全冻结 final-test 报告下保持方向稳定。
- **Why this block exists**: 专家第 2 点对 final-test hygiene 的质疑足以影响盲审通过概率。
- **Dataset / split / task**: Lending Club full rows；month-blocked seven-role split；final_test 不参与任何选择。
- **Compared systems**:
  - Primary: selected calibrated source by frozen `calibration_select` rule。
  - References: no-review cost-sensitive, all-review, capacity-aware 5/10/20/50, random review, uncertainty review, conformal review。
  - Optional selected baselines: LR/sigmoid and XGB/sigmoid only if pre-registered。
- **Metrics**: selected-source probability metrics；decision expected/realized cost；capacity frontier；selected-only bootstrap CI。
- **Setup details**:
  - Reuse existing month-blocked implementation where possible。
  - Strictly separate `calibration_fit`、`calibration_select`、`policy_tune`、`risk_calibration`、`final_test`。
  - Save a `protocol_manifest.json` with run command, git commit if available, package versions, random seeds, config hash。
- **Success criterion**: qualitative story stable: selected source stable or pre-declared replacement; capacity frontier and cost-sensitive conclusions remain interpretable。
- **Failure interpretation**: instability becomes a thesis limitation and claim-control update, not a failed dissertation。
- **Table / figure target**: locked-final main result table and protocol appendix。
- **Priority**: MUST-RUN.

### Block 3: Capacity Frontier With Realized Uncertainty And Matched Baselines

- **Claim tested**: capacity-aware deferral is useful as a comparative allocation rule under stated assumptions, beyond the mechanical monotonicity of expected optimization。
- **Why this block exists**: 专家第 3 点指出单调下降大部分由排序规则构造，必须转向 realized cost、CI、月份稳定性和 matched baselines。
- **Dataset / split / task**: Locked final_test predictions；use month-blocked final_test as primary。
- **Compared systems**:
  - Expected frontier: D-CRED benefit rank。
  - Realized frontier: same selected cases, final-test realized labels。
  - Baseline frontier: random review、uncertainty-band review、split conformal review、empirical conformal risk-control review。
  - Oracle upper bound: choose best realized-review-benefit cases, clearly marked as unattainable。
- **Capacity grid**: 1%、2%、5%、10%、20%、30%、50%。
- **Metrics**:
  - expected cost, realized cost, savings vs no review, savings vs all review。
  - block/month bootstrap 95% CI for realized cost and savings。
  - monthly frontier stability and rank correlation between expected benefit and realized benefit。
- **Setup details**:
  - CI unit should prefer issue-month block bootstrap; if months are too few at final_test, report both month bootstrap and observation bootstrap with caveat。
  - Plot all baselines on the same frontier figure, not separate tables。
- **Success criterion**: D-CRED benefit rank is competitive with or clearly characterized relative to interpretable baselines。
- **Failure interpretation**: If uncertainty/conformal/random matches or beats it, main claim becomes “frontier framework exposes allocation trade-offs”，not “D-CRED allocation dominates”。
- **Table / figure target**: main capacity frontier figure with CI; appendix monthly stability table。
- **Priority**: MUST-RUN.

### Block 4: Cost-Sensitivity Surface And Review Break-Even Analysis

- **Claim tested**: review value is conditional on explicit cost and human-quality regimes。
- **Why this block exists**: 专家第 4 点认为 FN:FP、review cost、rho 任意，且 99.1% review 说明 primary scenario 对复核太友好。
- **Dataset / split / task**: Locked final_test selected-source predictions and policy_tune thresholds。
- **Compared systems**: no-review、all-review、unrestricted reject option、capacity-aware deferral、random review、uncertainty/conformal review。
- **Grid**:
  - FN:FP = 2:1、5:1、10:1、20:1。
  - review cost = 0.01、0.05、0.1、0.2、0.5、1.0 times FP cost。
  - human residual `rho` = 0、0.05、0.1、0.2、0.5。
  - review capacity = 1%、5%、10%、20%、50%。
- **Metrics**:
  - expected cost, realized cost, review rate, automation rate, approval rate, savings vs no review/all review。
  - policy winner map by grid cell。
  - near-all-review region where unrestricted reject option reviews more than 80%、90%、95%。
- **Break-even derivation**:
  - Manual review cost for case `i`: `C_M(i)=c_R+rho*min(C_A(i), C_D(i))`。
  - Review is beneficial iff `c_R < (1-rho)*min(C_A(i), C_D(i))`。
  - Use this condition to explain when cheap high-quality review collapses toward all-review。
- **Setup details**:
  - Run as post-model evaluation over saved predictions; no retraining unless locked predictions are unavailable。
  - Report primary scenario but do not privilege it as universal。
- **Success criterion**: The dissertation can show exactly where review helps, where it saturates, and where no-review is better。
- **Failure interpretation**: If D-CRED is useful only in a subset of regimes, that is a stronger and more honest MSc result。
- **Table / figure target**: heatmap/surface figure, break-even explanation box, appendix grid table。
- **Priority**: MUST-RUN.

### Block 5: Cash-Flow Utility-Approval Frontier

- **Claim tested**: cash-flow objective changes policy ranking under comparable approval-rate constraints。
- **Why this block exists**: 专家第 6 点指出 tuned cash model 以约 0.74% approval rate 获胜，不能直接和正常批准率策略比较。
- **Dataset / split / task**: `dean_cashflow_full` terminal accepted-loan sample；month-blocked final_test；accepted/funded-loan scope only。
- **Compared systems**:
  - PD ranking。
  - predicted cash ranking。
  - hybrid ranking，例如 calibrated PD risk filter + cash ranking 或 weighted PD/cash score。
  - random approval baseline。
  - optional oracle cash ranking as upper bound, clearly marked unattainable。
- **Approval-rate grid**: 1%、5%、10%、20%、30%、50%、65%。
- **Metrics**:
  - mean net_cash, total net_cash, default rate, approval rate。
  - missed-profitable-loan opportunity cost。
  - approved-loss-making-loan loss。
  - block/month bootstrap CI。
  - cash model R2/MAE and explicit note if R2 remains negative。
- **Setup details**:
  - Do not rank policies by unconstrained threshold only。
  - A `coverage_constrained_best_policy.csv` should identify best policy at each approval rate。
  - The existing tuned cash low-approval result becomes a point on the frontier, not the headline win。
- **Success criterion**: The cash-flow section can say “cash-flow objective changes the frontier” rather than “one almost-no-loan strategy wins”。
- **Failure interpretation**: If PD ranking dominates under most approval rates, write that cash-flow regression is currently weak and scope the claim down。
- **Table / figure target**: utility-approval curve and constrained policy table。
- **Priority**: MUST-RUN.

### Block 6: Responsible-Credit Audit

- **Claim tested**: D-CRED can expose deployment risk across borrower/product/proxy groups, without claiming legal compliance。
- **Why this block exists**: 专家第 8 点指出 deployment-oriented 论文不能完全缺 fairness、subgroup calibration、adverse-action 风险暴露。
- **Dataset / split / task**: Locked final_test for PD/cost/review policies; `dean_cashflow_full` final_test for cash utility if group fields align。
- **Groups**:
  - `addr_state`。
  - `zip3` or state cluster, with small-cell suppression。
  - `home_ownership`。
  - income or revenue decile。
  - `loan_amnt` decile。
  - `purpose`。
- **Compared systems**:
  - primary locked D-CRED policy。
  - no-review baseline。
  - capacity-aware review at 5%、10%、20%。
  - with zip-code/proxy features vs without zip-code/proxy features。
- **Metrics**:
  - approval rate, rejection rate, review rate, default rate。
  - Brier, ECE, mean utility, realized cost。
  - subgroup calibration curves and reliability bins。
  - max/min group gaps and small-cell flags。
- **Setup details**:
  - This is a risk exposure audit, not a fairness compliance certificate。
  - Use no protected-class inference unless explicitly sourced and justified。
  - Small groups should be suppressed or aggregated to avoid noisy claims。
- **Success criterion**: The paper can honestly say it includes a minimum responsible-credit risk exposure analysis。
- **Failure interpretation**: Any large subgroup gaps become limitations and future work, not hidden defects。
- **Table / figure target**: responsible-credit audit table, subgroup calibration appendix。
- **Priority**: MUST-RUN.

### Block 7: Full Feature Audit And Strict/Default/Expanded Stress Test

- **Claim tested**: application-time feature protocol is systematic rather than a small hand-picked leakage table。
- **Why this block exists**: 专家第 11 点 says the current feature audit is too coarse and does not prove all post-origination/policy-generated/outcome-dependent fields were reviewed。
- **Dataset / split / task**: Lending Club primary data and accepted-loan `loan.csv` where relevant。
- **Feature categories**:
  - application-time。
  - underwriting-policy-generated。
  - post-origination。
  - repayment outcome。
  - administrative。
  - text。
  - timestamp。
  - uncertain / requires manual adjudication。
- **Compared feature sets**:
  - `strict`: only variables clearly available before underwriting and not strong proxies for lender policy outputs。
  - `default`: current D-CRED granting-stage protocol。
  - `expanded`: intentionally includes policy-generated or borderline fields for stress testing, never as clean deployment protocol。
- **Metrics**:
  - model AUC/PR-AUC, Brier/ECE/NLL。
  - decision expected/realized cost, approval/review rates。
  - cash-flow utility if the feature set applies to `loan.csv`。
  - delta from strict to default to expanded。
- **Setup details**:
  - Produce `all_fields_feature_audit.csv` with one row per raw field, category, allowed flag, reason, and source note。
  - Any expanded-set performance improvement must be interpreted as possible leakage/policy-proxy risk。
- **Success criterion**: The thesis can defend application-time control as an audited protocol, not just a keyword filter。
- **Failure interpretation**: If strict set performs worse, that supports the trade-off discussion; if expanded set performs better, it demonstrates why contaminated features are dangerous。
- **Table / figure target**: feature audit appendix and strict/default/expanded stress-test table。
- **Priority**: MUST-RUN.

### Block 8: Claim-Control And Dissertation Integration

- **Claim tested**: New experiments can be translated into safe thesis claims without overclaiming。
- **Why this block exists**: The expert's global verdict is “重大修改后通过”; the experiment plan only matters if the final paper claims match the evidence。
- **Dataset / split / task**: All outputs from B0-B7。
- **Compared systems**: Not applicable; this is synthesis and audit。
- **Metrics**: claim-supported status, table-to-claim traceability, unresolved limitations。
- **Setup details**:
  - Write `CLAIMS_FROM_RESULTS_BLIND_REVIEW_YYYYMMDD.md` after results are generated。
  - Every numeric statement in the thesis must link to a CSV/JSON/MD source。
  - Update `paper_writing_handoff_20260511/README_中文文件说明.md` only after the experiments are actually run。
- **Success criterion**: The dissertation can move from “defensive technical report” to a coherent MSc thesis with narrowed, evidence-backed claims。
- **Failure interpretation**: If some experiments are negative, preserve them and adjust the thesis, rather than changing the story around them。
- **Table / figure target**: claim audit appendix and revised result-to-claim matrix。
- **Priority**: MUST-RUN after experiments.

## Run Order And Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 | Freeze protocol and reviewer coverage | BR001-BR004 | `frozen_config.yaml` exists, config/data/split hashes recorded, old post-hoc outputs labeled | CPU minutes | If the config is written after running, locked claim is invalid |
| M1 | Build feature and group audit substrate | BR101-BR105 | all fields categorized; responsible-credit groups defined with small-cell rules | 0.5-1 day manual+CPU | Field semantics may be ambiguous |
| M2 | Run locked final and layer ablation | BR201-BR205 | selected-only final report and D-CRED ablation table generated | 2-8 GPU-hours or CPU/GPU mixed | Full-data tree runs may be slow |
| M3 | Evaluate capacity frontier, uncertainty, baselines | BR301-BR305 | same-figure frontier and CI tables written | CPU hours | Bootstrap over many capacities may be slow |
| M4 | Run cost/human-residual sensitivity | BR401-BR404 | full sensitivity surface and break-even table written | CPU hours | Large grid can become hard to summarize |
| M5 | Run cash-flow approval frontier | BR501-BR505 | constrained approval-rate curves and CI written | CPU hours | Cash model may remain weak |
| M6 | Run responsible-credit and feature-stress analyses | BR601-BR607 | subgroup audit and strict/default/expanded comparison written | 1-2 days CPU+manual | Sparse groups or proxy effects may complicate wording |
| M7 | Claim-control and thesis integration | BR701-BR704 | result-to-claim update and dissertation table map complete | 0.5-1 day | Overclaiming risk remains highest |

## Compute And Data Budget

- **GPU-hours**: 2-8 expected if rerunning full LightGBM/XGBoost locked models; 0 if reusing frozen predictions for post-model grids only.
- **CPU time**: 6-18 hours for sensitivity grids, bootstrap CIs, subgroup metrics, and feature-set stress tests depending on bootstrap repetitions.
- **Storage**: plan for 5-15 GB for predictions, bootstrap summaries, strict/default/expanded outputs, and audit tables.
- **Data preparation needs**:
  - Lending Club primary/granting data for locked D-CRED run.
  - `loan.csv` terminal accepted-loan sample for observed cash-flow frontier.
  - Full raw headers for field-level audit.
- **Human evaluation needs**: none, but feature-category adjudication needs manual review and should be tracked as audit decisions.
- **Biggest bottleneck**: field-level audit quality and claim-control, not model training.

## Risks And Mitigations

- **Risk: retroactive locked-final claim**.
  - **Mitigation**: create a new output directory named `locked_final_protocol`; do not rewrite history for older runs.
- **Risk: capacity frontier still looks mechanical**.
  - **Mitigation**: demote expected monotonicity to method property; lead with realized CI and matched baseline comparison.
- **Risk: cost sensitivity weakens the primary scenario**.
  - **Mitigation**: treat this as the intended result: D-CRED identifies where review is economically justified.
- **Risk: cash-flow frontier shows cash model weak outside low approval rates**.
  - **Mitigation**: write a constrained decision-analysis conclusion, not a cash-prediction success claim.
- **Risk: responsible-credit audit reveals subgroup gaps**.
  - **Mitigation**: report them as deployment risk exposure and future work; do not claim compliance.
- **Risk: feature audit finds ambiguous fields**.
  - **Mitigation**: mark as uncertain or excluded in strict set; use default/expanded comparison to quantify sensitivity.
- **Risk: too many tables for main dissertation**.
  - **Mitigation**: main paper keeps one ablation table, one locked-final table, one capacity frontier, one cost surface, one cash-flow frontier, one responsible-credit table; full grids go to appendix.

## Final Checklist

- [ ] Expert point 1 covered by D-CRED layer ablation table.
- [ ] Expert point 2 covered by `locked_final_protocol` and frozen config.
- [ ] Expert point 3 covered by realized frontier CI and matched baselines.
- [ ] Expert point 4 covered by cost-sensitivity surface and break-even derivation.
- [ ] Expert point 6 covered by approval-constrained cash-flow frontier.
- [ ] Expert point 8 covered by responsible-credit audit.
- [ ] Expert point 11 covered by all-field audit and strict/default/expanded feature stress test.
- [ ] Main paper tables are covered.
- [ ] Novelty is isolated as deployment-evaluation contribution.
- [ ] Simplicity is defended by avoiding new model SOTA claims.
- [ ] Frontier contribution is explicitly not claimed.
- [ ] Must-run items are separated from appendix-only diagnostics.
- [ ] Negative or mixed results are preserved in claim-control.
