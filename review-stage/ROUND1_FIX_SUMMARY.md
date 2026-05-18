# Round 1 Fix Summary

## Claim-Control Summary

- C1 is narrowed: temporal evaluation changes the deployment environment; it is not framed as uniformly worse than random split.
- C2 is supported: calibration changes Brier/ECE and can differ from ranking metrics.
- C3 is supported: cost-aware thresholds reduce expected cost versus fixed 0.5 on Lending Club.
- C4 is narrowed: split conformal is a conservative review-heavy control layer, not a high-automation deployment win.
- C5 is partial: UCI/German are reduced-protocol sanity checks, summarized across three seeds with no temporal claim.

## Limitations To Carry Into The Dissertation

- RF is a LightGBM random-forest surrogate and RF/XGB fit on a stratified 50k training cap.
- Validation data are reused for calibration, threshold selection, and conformal quantile estimation.
- Bootstrap CIs use a deterministic 50k test-observation subset for local stability.
- Reduced-protocol UCI/German results use three seeds and should be treated as sanity checks.
- The feature audit is a curated application-time protocol for the granting dataset, not a raw-feature contamination stress test.
- Reviewed cases are modeled as incurring review cost only; residual manual-review error is not estimated.
- Lending Club split conformal behaves mostly as approve-or-review at the reported operating point: about 91% review, 8-9% automatic approval, and near-zero automatic rejection.

## Lending Random vs Temporal

| dataset      | split    | model   | calibration   | partition   |   rows |   default_rate |   roc_auc |   pr_auc |        f1 |   balanced_accuracy |    brier |      nll |        ece |      mce |
|:-------------|:---------|:--------|:--------------|:------------|-------:|---------------:|----------:|---------:|----------:|--------------------:|---------:|---------:|-----------:|---------:|
| lending_club | random   | lr      | raw           | test        | 269537 |       0.199787 |  0.660411 | 0.314122 | 0.388831  |            0.61386  | 0.230836 | 0.653421 | 0.274627   | 0.625933 |
| lending_club | random   | rf      | raw           | test        | 269537 |       0.199787 |  0.650079 | 0.307001 | 0.38042   |            0.605263 | 0.231753 | 0.654816 | 0.279646   | 0.308748 |
| lending_club | random   | xgb     | raw           | test        | 269537 |       0.199787 |  0.65983  | 0.31511  | 0.0194553 |            0.503774 | 0.151605 | 0.473742 | 0.00307864 | 0.228799 |
| lending_club | temporal | lr      | raw           | test        | 269537 |       0.217933 |  0.672467 | 0.344533 | 0.418377  |            0.622972 | 0.222142 | 0.638014 | 0.242061   | 0.615756 |
| lending_club | temporal | rf      | raw           | test        | 269537 |       0.217933 |  0.661967 | 0.338741 | 0.407291  |            0.614343 | 0.220673 | 0.632082 | 0.243783   | 0.25663  |
| lending_club | temporal | xgb     | raw           | test        | 269537 |       0.217933 |  0.672005 | 0.349054 | 0.0133143 |            0.502545 | 0.162109 | 0.499409 | 0.0457322  | 0.394198 |

## Lending Cost And Selective Decision Summary

| model   |   fixed_0.5_cost |   cost_5_to_1_cost |   cost_5_to_1_delta |   cost_5_to_1_approval_rate |   cost_5_to_1_approved_default_rate |   robust_cost |   robust_approval_rate |   robust_approved_default_rate |   split_conformal_coverage |   split_conformal_automation_rate |   split_conformal_review_rate |   split_conformal_approved_default_rate |   split_conformal_expected_cost |
|:--------|-----------------:|-------------------:|--------------------:|----------------------------:|------------------------------------:|--------------:|-----------------------:|-------------------------------:|---------------------------:|----------------------------------:|------------------------------:|----------------------------------------:|--------------------------------:|
| lr      |          1.06562 |           0.664547 |           -0.401073 |                    0.352345 |                            0.111077 |      0.724887 |              0.0934417 |                      0.0646788 |                   0.898433 |                         0.0934417 |                      0.906558 |                               0.0646788 |                        0.120874 |
| rf      |          1.07973 |           0.676671 |           -0.403062 |                    0.33795  |                            0.114689 |      0.732846 |              0.0779151 |                      0.061378  |                   0.900641 |                         0.0779151 |                      0.922085 |                               0.061378  |                        0.11612  |
| xgb     |          1.0753  |           0.665612 |           -0.409691 |                    0.37058  |                            0.114291 |      0.711179 |              0.120662  |                      0.0687513 |                   0.897435 |                         0.0903512 |                      0.909649 |                               0.0602588 |                        0.118197 |

## Split-Conformal Operating Point

| model   |   split_conformal_expected_cost |   split_conformal_automation_rate |   split_conformal_review_rate |
|:--------|--------------------------------:|----------------------------------:|------------------------------:|
| lr      |                        0.120874 |                         0.0934417 |                      0.906558 |
| rf      |                        0.11612  |                         0.0779151 |                      0.922085 |
| xgb     |                        0.118197 |                         0.0903512 |                      0.909649 |

## Reduced-Protocol Best Cost Policies

| dataset       | model   | policy                  |   expected_cost_mean |   approval_rate_mean |   approved_default_rate_mean |
|:--------------|:--------|:------------------------|---------------------:|---------------------:|-----------------------------:|
| german_credit | lr      | profit_lgd_0.4_roi_0.15 |             0.6      |             0.51     |                    0.135126  |
| german_credit | rf      | profit_lgd_0.6_roi_0.1  |             0.566667 |             0.293333 |                    0.0924321 |
| german_credit | xgb     | profit_lgd_0.4_roi_0.15 |             0.568333 |             0.381667 |                    0.108629  |
| uci_default   | lr      | cost_5_to_1             |             0.636444 |             0.693056 |                    0.132485  |
| uci_default   | rf      | cost_5_to_1             |             0.557278 |             0.559556 |                    0.100193  |
| uci_default   | xgb     | cost_5_to_1             |             0.553778 |             0.559389 |                    0.0988521 |
