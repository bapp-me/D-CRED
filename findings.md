# Findings

## 2026-05-04: D-CRED Auto Review Loop

- Result: READY for MSc dissertation results chapter with limitations.
- Supported: calibration improves probability quality; cost-aware thresholding reduces expected cost versus fixed 0.5; temporal evaluation changes the operating environment; reduced UCI/German provide sanity checks.
- Partial: split conformal reduces expected cost only under the stated cheap-review, cost-only manual-review assumption and is review-heavy on Lending Club.
- Not supported: high-automation selective deployment, top-venue method novelty, production-bank deployment validity, or uniform model-family dominance.
- Required limitation language: 50k tree cap, LightGBM-RF surrogate, validation reuse, deterministic 50k bootstrap subset, three reduced seeds, curated feature audit, and no residual manual-review error model.

## 2026-05-18: Teacher Review P0/P1 Hard Review

- Result: ALMOST READY before final writing integration; P1 analyses are useful, but P0 audit output is keyword screening only.
- Supported: temporal evidence is mainly upward base-rate shift with modest PSI/KS feature movement; cost-aware thresholding is strongest under matched stated FN:FP ratios.
- Partial: selective conformal offers limited low-risk automation with heavy review, but is cost-dominated by all-review at review-cost multiplier 0.10 under perfect-review assumptions.
- Stress test: manual-review residual-error sensitivity compares selective review against automated threshold baselines only; it does not estimate real reviewer performance or prove selective dominance over all-review.
- Required writing placement: main text for bounded temporal default-rate summary, FN:FP 5:1 cost-aware thresholding, and selective operating point with all-review caveat; appendix/limitations for PSI/KS, alpha grids, cohort profile, profit scenarios, validation reuse, and manual-review sensitivity.
