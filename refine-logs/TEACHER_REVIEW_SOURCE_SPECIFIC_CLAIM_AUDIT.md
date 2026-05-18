# Teacher Review Source-Specific Claim Audit

Date: 2026-05-18

## Scope

This audit responds to the hard-review finding that the generated P0 audit was only keyword screening. It checks the current D-CRED claim-control files and the NTU dissertation source for the specific overclaim risks raised by the teacher-review P0/P1 supplement.

Sources scanned:

- `D-CRED/README.md`
- `D-CRED/CLAIMS_FROM_RESULTS.md`
- `D-CRED/refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md`
- `D:\code\diss_codex\ntu-dissertation\latex\chapter-*`
- `D:\code\diss_codex\ntu-dissertation\latex\c-front-matter`
- `D:\code\diss_codex\ntu-dissertation\latex\c-back-matter`

## Changes Made Before This Audit

- Replaced title-level `Deployment-Ready` wording with `Deployment-Oriented` in `README.md`, `chapter-1.tex`, `title-page.tex`, and `acronyms.tex`.
- Updated `CLAIMS_FROM_RESULTS.md` so the 2026-05-18 manual-review residual-error sensitivity is no longer listed as future work.
- Added an explicit all-review caveat to `CLAIMS_FROM_RESULTS.md`, `chapter-1.tex`, `chapter-5.tex`, `chapter-6.tex`, `chapter-7.tex`, and `abstract.tex`.
- Relabeled the P0 claim-control table as keyword screening rather than a final source-specific PASS.

## Source-Specific Findings

| Source | Finding | Status |
|---|---|---|
| `README.md` | Project descriptor now says `Deployment-Oriented Credit Risk Evaluation and Decisioning`. | OK |
| `CLAIMS_FROM_RESULTS.md` | C4 now says split conformal is cost-dominated by all-review at review-cost multiplier 0.10 under perfect-review assumptions. | OK |
| `CLAIMS_FROM_RESULTS.md` | Manual-review residual-error sensitivity is now a completed stress test against automated threshold baselines, not measured reviewer quality. | OK |
| `chapter-1/chapter-1.tex` | D-CRED expansion and contribution wording now avoid deployment-ready and cost-dominance language. | OK |
| `chapter-5/chapter-5.tex` | Results chapter now states split-conformal deltas are against automated threshold baselines and adds the all-review cost caveat. | OK |
| `chapter-6/chapter-6.tex` | Discussion chapter now states all-review can be cheaper under low perfect-review cost and scopes residual-error sensitivity as stylized. | OK |
| `chapter-7/chapter-7.tex` | Conclusion now rejects high-automation and selective cost dominance claims; future work asks for real manual-review performance data or stronger simulation. | OK |
| `c-front-matter/abstract.tex` | Abstract now states split conformal is limited automation with explicit review burden, not all-review cost dominance. | OK |
| Remaining hits for `high-automation`, `production-bank`, `fairness`, `reject inference`, and `ROI` | These appear as limitations, unsupported claims, or appendix/scenario labels rather than positive claims. | OK |

## Residual Limitations To Preserve

- The P0 keyword-screening table remains only a screening aid.
- The residual-error stress test is not real manual-review evidence.
- The all-review reference is a simplified benchmark under the same perfect-review assumption, not a production operating recommendation.
- Profit/LGD/ROI rows remain scenario analyses and should not enter the main ROI claim.

## Audit Verdict

The teacher-review P0/P1 supplement is source-consistent after the edits above, provided final writing keeps the selective decisioning claim narrow: review-heavy, limited automation, transparent review burden, and no all-review cost dominance.
