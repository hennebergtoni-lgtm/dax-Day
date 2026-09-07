# MASTERSTAND — DAX Daytrading Bot

Updated: 2026-09-08

This document is the durable project handover/source-of-truth. New work must preserve these constraints and verified findings.

## 1. Infrastructure milestone
The former notebook-centric Colab + Google Drive workflow became the main productivity bottleneck: repeated notebook prototypes, uploads, Drive mounts, namespace/path errors and reruns consumed hours without advancing research. The project therefore moves to a durable three-layer architecture:

1. BOT / STRATEGY CORE
2. DATA LAYER / RESEARCH DATABASE
3. RESEARCH & TEST LAB

GitHub repository `hennebergtoni-lgtm/dax-Day` is now the central code/version-control source. ChatGPT/Codex GitHub read/write access was proven on 2026-09-07 by a successful commit. Drive is no longer the development backbone.

## 2. Immutable reference baseline
- V11.2 remains unchanged and frozen.
- New hypotheses/variants never silently become the bot.
- Historical basis: 2014–2019.
- 1,673 valid Berlin session days.
- 481,824 raw M5 rows (1,673 daily files × 288 bars/day).
- 172,319 M5 Berlin-session bars (1,673 × 103). Earlier project notes that called this number “M1 candles” were mislabeled; the underlying data and strategy results are unchanged.
- 103 M5 session bars/day.
- Session 09:00–17:30 Europe/Berlin.
- Audited basis: 0 OHLC errors and 0 duplicate UTC timestamps.
- Audited session OHLC SHA256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`.
- Audited migration ZIP SHA256: `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`.
- V11.2 parameter grid: 144 variants.
- Walk-forward: 81 WFs, Train 45d, OOS 20d, Step 20d.
- Reference OOS: 36 positive, 45 negative, 0 flat WFs; 1,384 trades; -68.1095R.

## 3. Exact/FAST work retained
- Exact/FAST parity was established on the validated engine surface.
- FAST V2.8.18 executed 81 WFs × 144 variants × 3 cost models = 34,992 evaluations.
- Matrix aggregate normal-cost sum: -1122.231646R. This is a matrix sum, not one bot result.
- Observed acceleration around 1.243×.
- Exact engine SHA256: `9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887`.
- Known core bootstrap: 172,319 M5 session bars / 1,673 days; 144-grid; 81-WF schedule; trade-bearing pre-gate 14 trades, return_r 3.9351648669, PF 1.5556035886; parity 144/144 with 114 trade-bearing cases.

## 4. Research findings retained
### V2.8.19
- OR15 median PF ~0.724 vs OR5 ~0.413.
- Retest slightly better than breakout.
- OR-mid better than OR-opposite.
- RR1.5 better than RR2.0 in aggregate.
- OR/ATR filter strongest clue: >0.20 matrix sum ~-126.95R; 0.20–0.60 ~-75.49R; none ~-919.79R.
- Diagnostic V119: OR15 / Retest / OR-mid / RR2.0 / OR-ATR >0.20; 45 positive / 36 negative WFs; median PF ~1.053; total ~-8.74R. Not a promoted bot.

### V2.8.21 controlled factorial
48 variants: OR 5/15 × breakout/retest × OR-mid/opposite × RR1.5/2.0 × OR/ATR none/>0.20/0.20–0.60, direction both, remaining controls unchanged.
81 WFs × 48 × 3 costs = 11,664 evaluations.
Stress-positive candidates include:
- V47 +39.23R normal / +27.28 stress1.5x / +24.92 stress2x
- V48 +38.26 / +26.32 / +23.97
- V39 +27.38 / +25.08 / +20.30
- V38 +27.35 / +25.04 / +20.25
- V2 +23.91 / +21.57 / +19.25
- V3 +23.32 / +20.99 / +18.70
These remain hypotheses.

## 5. Open research matrix
High priority: Bollinger Bands, Fibonacci retracement, close gaps, volatility filters, entry filters, exit/target logic.
Medium priority: time/session filters, additional market-structure filters.

Bollinger research: bandwidth/volatility, price position, band breakout, pullback/mean reversion, OR interactions. Existing BB cache work proved fast feature generation; first pilot had a timestamp/entry-time lookup mismatch and must not be repeated blindly.

Fibonacci research: retracement after defined OR/impulse, zones, confirmation, retest interactions.

Gap research: gap size/direction, intraday gap close, OR/day-structure interactions.

## 6. Research governance
- Test new topics individually, then targeted interactions.
- Preserve V11.2 factors as controls.
- Avoid combinatorial explosion.
- No subjective cherry-picking.
- No single-WF parameter changes.
- No forced trades: no setup = no trade.
- No live/API promotion before validation.
- Required promotion flow:
  IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL -> COMBINATION TEST -> CANDIDATE BOT -> WF/OOS -> NEW BOT VERSION
- Candidate release requires OOS, cost stress, WF stability, overfitting checks and independent validation.

## 7. New engineering doctrine
- One durable core, not a notebook chain.
- Deterministic execution semantics and conservative intrabar handling.
- Explicit data/session contracts and hashes.
- Reproducible experiment manifests and result registry.
- Resume/checkpoint support for long research runs.
- CI tests for parity, no-lookahead, intrabar ambiguity, WF scheduling and cost stress.
- Large historical data should not be committed to public GitHub; use reproducible storage/cache with manifests and hashes.
- MT5 belongs behind a separate execution boundary; research and live execution must not be coupled.

## 8. Current milestone
1. Repository skeleton and CI — complete.
2. Contracts / parity / no-lookahead / intrabar / WF tests — complete foundation.
3. Frozen V11.2 recovered engine sources with SHA gates — complete.
4. Gate 0 audited historical M5 data + independent fingerprint — GREEN on 2026-09-08.
5. Gate 1 full V11.2 parity in the new lab — next.
6. BB001 isolated pilot after Gate 1.
7. FIB001, GAP001, EVENT001 and targeted interactions only after isolated evidence.
