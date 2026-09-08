# FIB001 Confirmed Breakout Impulse V1

Status: BINDING RESEARCH SPEC / DESCRIPTIVE ONLY / NO PROMOTION

## Why this exists
The first OR-completed impulse pilot produced negative evidence: session-open to directional OR-extreme measured post-breakout extension rather than retracement. That result is retained. This second anchor family tests a different, predeclared mechanism without changing the failed rule after seeing its output.

## Start rule
A confirmed-breakout impulse may exist only after a completed M5 candle closes beyond the completed opening-range boundary in the trade direction.

For a long breakout:
- breakout boundary = completed OR high;
- start price = OR high;
- start state time = breakout-confirmation candle time/state;
- no intrabar breakout is sufficient.

For a short breakout:
- breakout boundary = completed OR low;
- start price = OR low;
- start state time = breakout-confirmation candle time/state.

## End/freeze rule
The directional extreme may advance only while successive completed candles make a new directional extreme.

The impulse freezes at the first completed candle after breakout confirmation that fails to extend the directional extreme:
- long: first completed candle whose high does not exceed the current impulse high;
- short: first completed candle whose low does not fall below the current impulse low.

The impulse end price is the last causally observed directional extreme before that failure-to-extend candle. The anchor confirmation/freeze time is the completed failure-to-extend candle state time, not the earlier extreme candle timestamp.

## Retracement observation rule
A retracement observation is eligible only when:

`anchor_freeze_time < retracement_observation_time < entry_time`

Observations at or before the freeze time are rejected. If no frozen impulse exists before the trade observation, that trade is ineligible for this anchor family; it is not repaired using future bars.

## Forbidden adaptations
- choosing a later swing because it creates a Fibonacci-zone hit;
- looking forward until a convenient high/low appears;
- using the eventual session high/low;
- changing the failure-to-extend rule after reviewing P/L;
- replacing ineligible observations with another anchor family inside the same test.

## First test
1. generator unit tests;
2. future-pollution/prefix stability;
3. descriptive coverage and retracement distribution on the frozen 856-trade V11.2 evidence;
4. retain negative/low-coverage evidence if the rule is not useful;
5. no threshold tuning until descriptive causality is green.
