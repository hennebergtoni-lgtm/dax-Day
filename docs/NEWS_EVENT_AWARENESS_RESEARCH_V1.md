# News & Event Awareness Research V1

Status: RESEARCH / PLANNED — OBSERVATION FIRST, NO NEWS-DRIVEN EXECUTION
Updated: 2026-09-11

## Purpose

Capture the requirement that scheduled macro events and material breaking news can affect DAX volatility, energy prices, inflation expectations and intraday execution conditions.

The architecture must distinguish awareness from trading authority. News/event data may be collected continuously while the policy controlling how strategy admission reacts to it remains explicit, versioned and testable.

## 1. Preferred control model

Do not make the underlying event feed itself a casual ON/OFF switch. Prefer always-on event awareness with a selectable response policy.

Proposed future web label: `News / Event handling`

Conceptual modes:

- `OBSERVE_ONLY` — ingest/classify/display event context; never alter admission.
- `EVENT_GUARD` — scheduled/high-confidence events may temporarily block or reduce new entries under a separately tested policy.
- `NEWS_REACTIVE_RESEARCH` — research-only strategies may use event/news state as an input after historical/forward validation; never automatically promoted.

Current product state remains `OBSERVE_ONLY / PLANNED`; no external news feed is yet an authoritative runtime input.

## 2. Two distinct information channels

### A. Scheduled macro events

Examples:
- Federal Reserve / FOMC rate decisions and press conferences;
- ECB Governing Council monetary-policy decisions and press conferences;
- CPI/inflation releases;
- major employment releases;
- other predeclared high-impact macro events after explicit catalog approval.

Preferred sources are first-party calendars/releases when available. Scheduled events are deterministic enough to cache ahead of time and test historically.

### B. Unscheduled breaking news

Examples:
- geopolitical escalation/de-escalation;
- energy infrastructure/shipping disruptions;
- sudden sanctions/tariff announcements;
- emergency central-bank/government measures;
- other material market-moving events.

Breaking news requires stricter freshness, source-quality, duplicate and conflict handling than scheduled calendars. It must not be synchronously fetched from the internet inside the per-bar trading hot path.

## 3. Canonical EventContext proposal

A future immutable event record should minimally bind:

- `event_id`;
- `event_type` / category;
- source identity;
- source fingerprint / provenance;
- scheduled time when applicable;
- first observed time;
- last updated time;
- affected region/asset context;
- impact tier;
- scheduled vs breaking classification;
- freshness state;
- confidence/source-consensus state;
- policy state (`OBSERVE`, `GUARD`, later research action);
- expiry time;
- execution capability remains `NONE` for the current product stage.

Event identity and revisions must be deterministic and auditable. A changed headline must not silently rewrite earlier evidence.

## 4. EVENT_GUARD principles

The first useful production-adjacent application should be defensive rather than predictive.

Examples for later research:
- block new entries in a tested pre/post window around Tier-1 scheduled events;
- reduce allowed exposure under a separately validated risk policy;
- suppress FAST-M1 mode around unvalidated high-impact windows;
- expose a visible operator countdown/context banner.

No fixed window (for example 5/15/30 minutes) is approved by this document. It must be researched against DAX data and costs.

Open positions must have a separately researched policy. Do not automatically close an existing position merely because an event begins.

## 5. NEWS_REACTIVE_RESEARCH principles

Directly trading headline direction/sentiment is substantially harder than event avoidance.

Before any reactive news strategy can affect a decision:

1. historical timestamped event/news data must be available without lookahead;
2. source publication time vs ingestion time must be distinguished;
3. revisions/duplicates must be preserved;
4. source confidence/consensus must be explicit;
5. latency from publication to bot observation must be modelled;
6. no LLM-generated interpretation may directly authorize an order;
7. strategy effect must pass backtest/OOS/WF/multiple-testing and forward SHADOW gates;
8. cost/slippage/gap stress is mandatory;
9. unscheduled-event false positives must be measured.

## 6. Hot-path architecture

Preferred flow:

`external official/news sources -> background collector/cache -> validated EventContext store -> read-only EventRiskSnapshot -> admission/risk policy`

The strategy bar loop should read a compact already-validated snapshot. It should not perform web searches, scrape articles or wait on remote news APIs.

This mirrors the broader project architecture: external data collection/reconciliation is separated from causal strategy decisions.

## 7. Multi-timeframe interaction

FAST-M1 and news awareness must be validated jointly before simultaneous activation.

Because one-minute trading has a smaller expected move and more sensitivity to spread/slippage/gaps, the default research hypothesis is conservative:

- high-impact event uncertainty should not automatically enable FAST mode;
- EVENT_GUARD may disable/suppress new FAST entries unless a dedicated news-volatility M1 candidate later proves an edge;
- the M5 candidate and FAST-M1 candidate may receive the same EventRiskSnapshot but keep separate policy/evidence.

## 8. Public-system reuse lessons

- Mature systems separate scheduled events from ordinary market-data callbacks rather than sprinkling time checks throughout entry logic.
- Protection/gating mechanisms are separate from strategy signal generation and can compose multiple safeguards.
- The project should therefore add event/news state as an independent context/gate, not bake headlines into CAND-001 entry code.

## 9. Initial source policy

For scheduled central-bank events prefer first-party official sources such as:
- Federal Reserve FOMC meeting calendar;
- ECB Governing Council / monetary-policy calendar and releases.

For breaking news, provider/source selection remains RESEARCH. The runtime must eventually support provenance, freshness, deduplication and fail-closed handling if a required feed becomes stale.

## 10. Promotion rule

Event awareness may be implemented as observation without trading authority first. Any mode that blocks/reduces/increases trading must receive its own policy version, regression tests, historical evaluation and forward SHADOW evidence before promotion. Any mode that actively trades news direction has a substantially higher evidence burden.
