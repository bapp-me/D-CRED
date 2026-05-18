# Findings

## 2026-05-04: D-CRED Auto Review Loop

- Result: READY for MSc dissertation results chapter with limitations.
- Supported: calibration improves probability quality; cost-aware thresholding reduces expected cost versus fixed 0.5; temporal evaluation changes the operating environment; reduced UCI/German provide sanity checks.
- Partial: split conformal reduces expected cost only under the stated cheap-review, cost-only manual-review assumption and is review-heavy on Lending Club.
- Not supported: high-automation selective deployment, top-venue method novelty, production-bank deployment validity, or uniform model-family dominance.
- Required limitation language: 50k tree cap, LightGBM-RF surrogate, validation reuse, deterministic 50k bootstrap subset, three reduced seeds, curated feature audit, and no residual manual-review error model.
