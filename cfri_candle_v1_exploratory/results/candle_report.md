# CFRI candle geometry: exploratory paired replay

This method was designed after the 2026 held-out results were seen. These are descriptive,
exploratory comparisons on the same 2026 targets and feature-wise masks; they are not
a new confirmatory holdout. The feature mask benchmark has no whole-row outage test.

Verified 816 paired conditions across 16 ETFs. 
Each condition uses the same target frame, feature mask, original CFRI, and SAITS V2 score.
All new price predictions use the original joint OHLC projection; observed cells stay fixed.

## Equal-ETF macro NRMSE

| Method | All five fields | OHLC only | Volume |
|---|---:|---:|---:|
| cfri_joint | 0.138867 | 0.050910 | 0.490697 |
| candle_direct | 0.136280 | 0.047676 | 0.490697 |
| candle_half | 0.135973 | 0.047293 | 0.490697 |
| saits_joint | 0.139900 | 0.046838 | 0.512149 |

## Paired wins by ETF

| Candidate | Comparator | All fields | OHLC only | Volume |
|---|---|---:|---:|---:|
| candle_direct | cfri_joint | 16/16 | 16/16 | 0/16 |
| candle_direct | saits_joint | 11/16 | 6/16 | 12/16 |
| candle_half | cfri_joint | 16/16 | 16/16 | 0/16 |
| candle_half | saits_joint | 11/16 | 8/16 | 12/16 |

## Gap length (equal ETF average)

| Block | Method | All fields | OHLC only |
|---:|---|---:|---:|
| 1 | candle_direct | 0.123463 | 0.041404 |
| 1 | candle_half | 0.123959 | 0.042024 |
| 1 | cfri_joint | 0.126474 | 0.045168 |
| 1 | saits_joint | 0.131827 | 0.039777 |
| 2 | candle_direct | 0.128365 | 0.043129 |
| 2 | candle_half | 0.128314 | 0.043065 |
| 2 | cfri_joint | 0.130653 | 0.045989 |
| 2 | saits_joint | 0.135109 | 0.042617 |
| 3 | candle_direct | 0.131314 | 0.044686 |
| 3 | candle_half | 0.131088 | 0.044403 |
| 3 | cfri_joint | 0.133527 | 0.047452 |
| 3 | saits_joint | 0.135460 | 0.043242 |
| 5 | candle_direct | 0.141304 | 0.047344 |
| 5 | candle_half | 0.141016 | 0.046984 |
| 5 | cfri_joint | 0.143700 | 0.050339 |
| 5 | saits_joint | 0.142385 | 0.047234 |
| 10 | candle_direct | 0.140061 | 0.051463 |
| 10 | candle_half | 0.138886 | 0.049995 |
| 10 | cfri_joint | 0.142074 | 0.053980 |
| 10 | saits_joint | 0.140543 | 0.051680 |
| 20 | candle_direct | 0.161618 | 0.063204 |
| 20 | candle_half | 0.160879 | 0.062281 |
| 20 | cfri_joint | 0.165726 | 0.068340 |
| 20 | saits_joint | 0.161163 | 0.061294 |

No method or blend weight was selected using these test scores. The direct
candidate and a fixed 50% log-price blend are both reported. All five feature
scores, per-condition data and SHA sidecars are included in the ZIP.
