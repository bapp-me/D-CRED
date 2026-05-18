# Claims From Results: D-CRED

Date: 2026-05-04

## Verdict

- claim_supported: partial
- confidence: medium-high for MSc dissertation claims; low for top-venue claims
- reviewer_status: READY for MSc dissertation results chapter; NOT READY for top venue

## Supported Claims

1. Temporal evaluation changes the deployment setting.
   - Lending Club temporal test has a higher default rate than random test and different ranking/calibration behavior.
   - The claim should not say temporal AUC is uniformly worse.

2. Calibration matters for probability quality.
   - Isotonic calibration is best by Brier for LR, RF-style LightGBM, and XGB on the temporal Lending Club split.

3. Cost-aware thresholding beats fixed 0.5 for the reported Lending Club cost setting.
   - At FN:FP = 5:1, `cost_5_to_1` reduces expected cost versus fixed 0.5 for all three temporal Lending Club models.
   - `decision_delta_ci.csv` gives paired bootstrap deltas with CIs below zero.

4. Selective decisioning is useful as a conservative risk-control analysis.
   - Under the corrected `false_positive_cost` review-cost basis, split conformal reduces expected cost at the reported operating point.
   - The result is review-heavy: about 91% review, about 8-9% automation, and near-zero automatic rejection.

5. UCI Default and German Credit support reduced-protocol sanity checks.
   - They support calibration/cost/selective-decision observations, not temporal-deployment claims.

## Not Supported

- General top-venue novelty or a new model contribution.
- Uniform model-family dominance.
- Uniform random-split overstatement of ROC-AUC.
- High-automation conformal selective deployment on Lending Club.
- Production-bank deployment validity without production data.
- Manual-review correctness; reviewed cases are modeled as cost-only with no residual manual-review error.

## Required Writing Limits

- RF is a LightGBM random-forest surrogate.
- RF/XGB fit on a stratified 50k training cap for local stability.
- Validation data are reused for calibration, threshold selection, and conformal quantile estimation.
- Bootstrap CIs use a deterministic 50k test-observation subset.
- Reduced UCI/German summaries use three seeds.
- Feature audit is a curated application-time protocol, not a contaminated raw-feature stress test.

## Revised Dissertation Claim

D-CRED is a deployment-ready credit-risk evaluation and decisioning framework. The evidence supports using leakage-aware temporal evaluation, probability calibration, and cost-aware thresholding as the core dissertation contribution. Selective conformal decisioning should be presented as a conservative review-heavy risk-control layer, not as a high-automation decision policy.

## Next Experiments If Target Shifts Beyond MSc

- Add a separate conformal-calibration holdout.
- Add manual-review residual-error sensitivity.
- Add rolling temporal splits.
- Add contaminated-feature stress test if raw policy-generated Lending Club fields are available.
- Run broader benchmarks or production-like credit data if available.
