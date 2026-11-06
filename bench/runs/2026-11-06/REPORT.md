# Design bench — 2026-11-06

Same briefs, same model, one skill per cell. Scores are deterministic (see `score.py`).

| skill | 01 | 02 | 04 | 08 | mean |
|---|---:|---:|---:|---:|---:|
| control | 84 | 79 | 92 | 85 | **85** |
| hallmark | 100 | 86 | 97 | 94 | **94** |
| huashu-design | 77 | 89 | 91 | 87 | **86** |
| impeccable | 84 | 87 | 100 | 84 | **89** |
| superdesign | 80 | 86 | 91 | 87 | **86** |
| ui-ux-pro-max | 83 | 85 | 94 | 85 | **87** |

## Detail

| cell | score | slop penalty | contrast fail | 375 overflow | seconds |
|---|---:|---:|---:|:--:|---:|
| control/01-saas-landing | 84 | -0 | 0.022 | no | 827.6 |
| control/02-dashboard | 79 | -4 | 0.055 | no | 613.9 |
| control/04-mobile-onboarding | 92 | -4 | 0.091 | no | 325.4 |
| control/08-admin-table | 85 | -0 | 0.05 | no | 542.4 |
| hallmark/01-saas-landing | 100 | -0 | 0.0 | no | 900.1 |
| hallmark/02-dashboard | 86 | -0 | 0.0 | no | 900.1 |
| hallmark/04-mobile-onboarding | 97 | -0 | 0.0 | no | 412.9 |
| hallmark/08-admin-table | 94 | -0 | 0.0 | no | 483.0 |
| huashu-design/01-saas-landing | 77 | -4 | 0.054 | no | 900.1 |
| huashu-design/02-dashboard | 89 | -0 | 0.011 | no | 697.4 |
| huashu-design/04-mobile-onboarding | 91 | -0 | 0.0 | no | 400.6 |
| huashu-design/08-admin-table | 87 | -0 | 0.0 | no | 740.7 |
| impeccable/01-saas-landing | 84 | -0 | 0.02 | no | 900.0 |
| impeccable/02-dashboard | 87 | -0 | 0.109 | no | 744.4 |
| impeccable/04-mobile-onboarding | 100 | -0 | 0.0 | no | 699.2 |
| impeccable/08-admin-table | 84 | -0 | 0.0 | no | 549.4 |
| superdesign/01-saas-landing | 80 | -4 | 0.0 | no | 707.2 |
| superdesign/02-dashboard | 86 | -0 | 0.0 | no | 809.9 |
| superdesign/04-mobile-onboarding | 91 | -0 | 0.2 | no | 364.6 |
| superdesign/08-admin-table | 87 | -0 | 0.0 | no | 429.4 |
| ui-ux-pro-max/01-saas-landing | 83 | -4 | 0.0 | no | 651.9 |
| ui-ux-pro-max/02-dashboard | 85 | -4 | 0.0 | no | 871.2 |
| ui-ux-pro-max/04-mobile-onboarding | 94 | -0 | 0.0 | no | 725.4 |
| ui-ux-pro-max/08-admin-table | 85 | -0 | 0.048 | no | 446.5 |
