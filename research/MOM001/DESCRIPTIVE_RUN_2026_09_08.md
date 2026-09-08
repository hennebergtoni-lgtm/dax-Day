# MOM001 — Corrected Descriptive Run 2026-09-08

Status: RESEARCH ONLY / OOS_DIAGNOSTIC_DERIVED / NOT PROMOTION PROOF.

## Timestamp correction
The paired MOM001/SESSION001 diagnostic pass was rerun after verifying that frozen reproduced trade timestamps are Berlin-session wall-clock values stored without an offset. The initial UTC interpretation was rejected.

Corrected validation:
- momentum feature eligible: 856/856 trades
- latest completed M5 state strictly before entry: 856/856
- state-time causality violations: 0

## Descriptive findings
Three completed directional candle bodies:
- `directional_closes_3 = -3`: 98 trades, -15.1001R, PF 0.7631
- `directional_closes_3 = 0`: 666 trades, -19.7907R, PF 0.9505
- `directional_closes_3 = +3`: 92 trades, +3.5815R, PF 1.0685

The superficially positive `+3` state is unstable:
- 2014 -1.2140R
- 2015 -5.1518R
- 2016 +12.3914R
- 2017 +2.0563R
- 2018 -3.4063R
- 2019 -1.0941R
- WF1-27 -5.8338R
- WF28-54 +13.9158R
- WF55-81 -4.5005R
- 51 active WFs: 24 positive / 27 negative; median active-WF R -0.3828R

Three-bar return sign relative to frozen V11.2 trade direction:
- ALIGNED: 636 trades, -28.8767R, PF 0.9250
- OPPOSED: 216 trades, -4.4027R, PF 0.9659
- FLAT: 4 trades, +1.9702R, too sparse to interpret

## Binding interpretation
No MOM001 selector is retained from this diagnostic run. The `+3` completed-candle state is not stable enough, and simple 3-bar momentum agreement does not improve the frozen V11.2 ledger. Any later momentum threshold/horizon change is a new hypothesis and requires fresh validation.
