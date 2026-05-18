# Claims From Results: D-CRED

Date: 2026-05-18

## Verdict

- claim_supported: partial
- confidence: medium-high for MSc dissertation claims; low for top-venue or production claims
- reviewer_status: ALMOST READY for integrating the 2026-05-18 teacher-review P0/P1 supplement; READY for MSc framing after the claim-control edits below are carried into the dissertation text

## Supported Claims

1. Temporal evaluation changes the deployment setting.
   - Lending Club temporal validation/test periods have higher default rates than the training period.
   - The 2026-05-18 PSI/KS diagnostics show modest feature movement; the safest interpretation is mainly base-rate shift plus limited application-time feature distribution movement.
   - The claim should not say temporal AUC is uniformly worse, causal temporal drift is proven, or random splits necessarily overstate every metric.

2. Calibration matters for probability quality.
   - Isotonic calibration is best by Brier for LR, RF-style LightGBM, and XGB on the temporal Lending Club split.
   - This supports probability-quality and decision-evaluation claims, not model-family dominance.

3. Cost-aware thresholding is the strongest quantitative result under stated assumptions.
   - At FN:FP = 5:1, `cost_5_to_1` reduces expected cost versus fixed 0.5 for all three temporal Lending Club models.
   - `decision_delta_ci.csv` gives paired bootstrap deltas with CIs below zero for the reported FN:FP = 5:1 decision claim.
   - The broader scenario table supports using thresholds matched to the stated cost ratio; it does not support a universal threshold or production ROI claim.

4. Selective decisioning is useful only as a conservative review-burden and risk-control analysis.
   - Split conformal at the reported operating point is review-heavy: about 91% review, about 8-9% automation, and near-zero automatic rejection.
   - It improves cost versus automated threshold baselines under the cheap-review assumption, but it is cost-dominated by all-review at review-cost multiplier 0.10 when reviewed cases are assumed perfectly resolved.
   - Therefore C4 should be written as limited automation of a low-risk approval cohort plus transparent review burden, not as cost-optimal selective deployment.

5. Manual-review residual-error sensitivity is now available as a stress test.
   - The 2026-05-18 sensitivity adds stylized residual classification-error cost to reviewed cases.
   - It compares selective review against automated robust/cost-threshold baselines; it does not measure real reviewer quality and does not prove dominance over all-review.

6. UCI Default and German Credit support reduced-protocol sanity checks.
   - They support calibration/cost/selective-decision observations, not temporal-deployment claims.

## Not Supported

- General top-venue novelty or a new model contribution.
- Uniform model-family dominance.
- Uniform random-split overstatement of ROC-AUC.
- High-automation conformal selective deployment on Lending Club.
- Selective conformal cost dominance over all-review under cheap perfect-review assumptions.
- Production-bank deployment validity or production ROI without production data.
- Fairness compliance, reject-inference correction, or manual-review correctness.

## Required Writing Limits

- RF is a LightGBM random-forest surrogate.
- RF/XGB fit on a stratified 50k training cap for local stability.
- Validation data are reused for calibration, threshold selection, and conformal quantile estimation.
- Bootstrap CIs use a deterministic 50k test-observation subset.
- Reduced UCI/German summaries use three seeds.
- Feature audit is a curated application-time protocol, not a contaminated raw-feature stress test.
- P0 claim-control tables generated on 2026-05-18 are keyword screening aids, not source-specific proof that every final dissertation paragraph is safe.
- Profit/LGD/ROI scenario tables are appendix scenario analyses only.

## Revised Dissertation Claim

D-CRED is a deployment-oriented credit-risk evaluation and decisioning framework. The evidence supports leakage-aware temporal evaluation, probability calibration, and cost-aware thresholding as the core MSc contribution. Selective conformal decisioning should be presented as a conservative, review-heavy risk-control analysis with limited automation and an explicit all-review caveat.

## Next Experiments If Target Shifts Beyond MSc

- Add a separate conformal-calibration holdout.
- Add rolling temporal splits.
- Add contaminated-feature stress test if raw policy-generated Lending Club fields are available.
- Add real manual-review performance data or a stronger reviewer simulation before making review-quality claims.
- Run broader benchmarks or production-like credit data if available.
