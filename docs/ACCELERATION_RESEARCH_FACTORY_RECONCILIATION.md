# Research Factory reconciliation — Step2234

All four original rescue anchors were fully read. Source extracted-text SHA256 is recorded in research/acceleration_program_v1.json; this is not a hash of original downloaded bytes. All40 H,100 F and24 learning IDs are retained with original mechanism/detection/reaction and actual existing repository paths. The checker validates cardinality, source IDs, owner existence, referenced test function existence, and bans unreviewed REAL_DEMO_VERIFIED promotion. Coverage is conservatively partial:42 rows point to local tests; status53 GAP/38 SYNTHETIC_ONLY/9 WAITING_EXTERNAL. A test reference can cover only one facet while its broader scenario stays GAP. Added PTC/session/identity references do not establish real broker truth. No case is represented as real IG broker evidence.

| Rescue source | Reconciliation |
| --- | --- |
| Drift review2026-09-13 | ALREADY_HAVE: five original P0 gaps addressed by2217–2230; confirm exact current tests for credential/heartbeat/execution/inventory/runbook. Real iPhone rendering external. |
| Hardening2 final | ALREADY_HAVE/EXTEND: preserve read-only console, canonical owners, strict context/overlap/state. Existing historical envelope requires actual pinned detail rows. |
| Factory3 final | EXTEND: source40/100/24 mapped below and in JSON; research ideas are not implemented or tested edge claims. |
| Post-DEMO A–J | IMPLEMENT/PREPARE when dependencies available: analytics and local failure work authorized by current user mandate. Real order/fill/TCA/parity/equity source remains WAITING_EXTERNAL. |

## Hypotheses

| ID | Stage | Mechanism | Available owner | Decision | Evidence / leakage / overfit / cost |
| --- | --- | --- | --- | --- | --- |
| H01 ATR compression | REGIME | Regime: niedrige vorab bekannte ATR; komprimierter OR als gespeicherte Bewegung | src/daxlab/research/atr_regime.py | PREPARE | B,D,P; ATR nur bis Decision; overfit M; cost L |
| H02 ATR expansion | REGIME | Regime: bereits bestätigte Expansion; Struktur fortgesetzter Ausbruch | src/daxlab/research/atr_regime.py | PREPARE | B,P; Keine spätere Sessionvolatilität; overfit M; cost L |
| H03 Daily ATR relation | REGIME | Regime: OR relativ zu abgeschlossenem Daily ATR | src/daxlab/research/atr_regime.py | PREPARE | B,D; Aktueller Tagesrange ist noch unvollständig; overfit M; cost L |
| H04 ADX enter/exit hysteresis | REGIME | Regime: getrennte Eintritt-/Austrittsschwellen statt Flips | src/daxlab/research/atr_regime.py | PREPARE | B; ADX nur abgeschlossene Bars; overfit M; cost L |
| H05 Minimum dwell time | REGIME | Regime bleibt für deklarierte Bars, sofern kein Safety-Block | src/daxlab/research/atr_regime.py | PREPARE | B,P; Dwell keine rückdatierte Klassifikation; overfit M; cost L |
| H06 Persistence requirement | REGIME | Regime erst nach konsekutiven kausalen Bestätigungen | src/daxlab/research/atr_regime.py | PREPARE | B; Kein rückwirkendes Regime-Label; overfit M; cost L |
| H07 Trend confirmation | REGIME | Regime: Trend, Struktur HH/HL oder LH/LL bestätigt | src/daxlab/research/market_structure.py | PREPARE | B,D; Pivot erst bei Bestätigung bekannt; overfit M; cost L |
| H08 Momentum confirmation | REGIME | Regime: Trend, Struktur Breakout; vergangenes Momentum | src/daxlab/research/momentum.py | PREPARE | B,Q; Keine Forward-Returns als Feature; overfit M; cost L |
| H09 Volatility circuit breaker | REGIME | Regime: beobachtbarer extremer Quote-/ATR-Stress | src/daxlab/research/atr_regime.py | PREPARE | B,Q,P; Keine ex-post „Crash“-Labels; overfit M; cost L |
| H10 Time-of-day regime | REGIME | Regime abhängig von Sessionphase | src/daxlab/research/session_context.py | PREPARE | B,Q; Sommer-/Winterzeit korrekt; overfit M; cost L |
| H11 Opening gap size | REGIME | Regime: Gap relativ zum abgeschlossenen Vortag/ATR | src/daxlab/research/gap_context.py | PREPARE | B,D; Research Close vs Broker Close abgleichen; overfit M; cost L |
| H12 Gap persistence | REGIME | Regime: Gap; Struktur hält Gap bis Decision | src/daxlab/research/gap_context.py | PREPARE | B,D; Nicht späteren Gap-Fill verwenden; overfit M; cost L |
| H13 VWAP relation | REGIME | Regime: Trend/Range separat; Lage zu echtem VWAP | src/daxlab/research/twap.py | LATER | B,V; CFD tick volume nicht ungeprüft Trade-Volumen; overfit H; cost M |
| H14 News stress observation | REGIME | Regime: veröffentlichter Kalender-/Eventkontext | src/daxlab/research/entry_diagnostics.py | LATER | B,Q,Publish-time; Kalenderrevision und surprise später bekannt; overfit H; cost M |
| H15 OR5 vs OR15 | STRUCTURE | Struktur: jeweils vollständig abgeschlossener OR im gleichen Regime | src/daxlab/research/market_structure.py | PREPARE | B,Q,P; OR15 nicht vor Minute15 bekannt; overfit M; cost L |
| H16 OR/ATR relative width | STRUCTURE | Struktur: zu eng/zu breit relativ zum Regime | src/daxlab/research/atr_regime.py | PREPARE | B,D; Completed OR/ATR; overfit M; cost L |
| H17 First breakout only | STRUCTURE | Struktur: erster kausaler CLOSED-Bar-Bruch des OR | src/daxlab/research/market_structure.py | PREPARE | B,P; Zähler aus damaligem State; overfit M; cost L |
| H18 Previous-day high | STRUCTURE | Struktur: OR-Bruch relativ zu vorbekanntem PDH | src/daxlab/research/market_structure.py | PREPARE | B,D; Vollständig vorangegangene Session; overfit M; cost L |
| H19 Previous-day low | STRUCTURE | Struktur: OR-Bruch relativ zu PDL | src/daxlab/research/market_structure.py | PREPARE | B,D,Q; Kein aktuelles Day Low; overfit M; cost L |
| H20 Previous-day range | STRUCTURE | Struktur: inside/outside Vor-Tagesrange | src/daxlab/research/market_structure.py | PREPARE | B,D; Vor-Tageskalender konsistent; overfit M; cost L |
| H21 Failed breakout | STRUCTURE | Struktur: bestätigter Bruch, später CLOSED-Rückkehr bereits beobachtet | src/daxlab/research/market_structure.py | PREPARE | B,P; Rückkehr nicht ursprünglichem Entry rückwirkend geben; overfit H; cost L |
| H22 Consolidation quality | STRUCTURE | Struktur: kausaler Pre-Breakout Range/Overlap | src/daxlab/research/market_structure.py | PREPARE | B; Keine nachträgliche Base-Abgrenzung; overfit H; cost L |
| H23 Breakout tightness | STRUCTURE | Struktur: lokal enger bestätigter Triggerbereich | src/daxlab/research/market_structure.py | PREPARE | B,Q,P; Anchors vor Entry bestätigt; overfit M; cost L |
| H24 First retest structure | STRUCTURE | Struktur: erster kausaler Retest nach bestätigtem Bruch | src/daxlab/research/market_structure.py | PREPARE | B,Q,P; Retest erst bei Abschluss klassifizieren; overfit H; cost L |
| H25 Delayed retest structure | STRUCTURE | Struktur: Zeit seit Bruch, Retest noch vor Session-Ende | src/daxlab/research/market_structure.py | PREPARE | B,P; Kein Wissen um späteren Trend; overfit M; cost L |
| H26 Breakout distance | ENTRY | Entry im Trend/OR-Breakout: Distanz der ersten CLOSED-Bar | src/daxlab/research/momentum.py | PREPARE | B,Q,P; Entscheidung erst nach Close; overfit M; cost L |
| H27 Wick/body quality | ENTRY | Entry im Breakout: bestätigte Kerzenform | src/daxlab/research/momentum.py | PREPARE | B,P; Keine Intrabar-Future-Bewegung; overfit H; cost L |
| H28 Close location | ENTRY | Entry im Breakout: Schluss nahe Ausbruchsseite | src/daxlab/research/momentum.py | PREPARE | B,P; Close erst nach Bar-Ende; overfit M; cost L |
| H29 Spread-aware admission research | ENTRY | Entry im gleichen Regime/Setup: beobachtbarer Spread relativ zu Stop | src/daxlab/research/momentum.py | PREPARE | B,Q,P; Research Mid ist kein Arrival Ask/Bid; overfit M; cost L |
| H30 Follow-through confirmation | ENTRY | Entry nach zusätzlicher CLOSED-Bar, Trend/Breakout | src/daxlab/research/momentum.py | PREPARE | B,Q,P; Neue Info nur neuer Decision-Zeitpunkt; overfit H; cost L |
| H31 Immediate reversal avoidance | ENTRY | Entry erst wenn beobachtete Gegenbewegung klassifiziert | src/daxlab/research/momentum.py | PREPARE | B,Q,P; Kein Future-Bar Ausschluss alter Entries; overfit H; cost L |
| H32 Fixed pullback percentages | ENTRY | Entry im Trend/Retest: 25/33/38.2/50% gleiche Anchors | src/daxlab/research/fibonacci_retracement.py | PREPARE | B,Q,P; Anchor bestätigter Impuls; overfit H; cost L |
| H33 ATR-normalized pullback | ENTRY | Entry im Trend/Retest: Rücklauf in ATR-Einheiten | src/daxlab/research/fibonacci_retracement.py | PREPARE | B,D,P; ATR vor Entscheidung; overfit M; cost L |
| H34 OR-normalized pullback | ENTRY | Entry im OR-Retest: Rücklauf relativ OR | src/daxlab/research/fibonacci_retracement.py | PREPARE | B,P; Vollständiger OR; overfit M; cost L |
| H35 Entry delay | ENTRY | Entry im selben Regime/Structure nach deklarierter Wartezeit | src/daxlab/research/entry_diagnostics.py | PREPARE | B,Q,P; Keine Best-price-after-signal Auswahl; overfit H; cost L |
| H36 Late-entry avoidance | ENTRY | Entry im Trend/Breakout: Extension und Sessionzeit | src/daxlab/research/session_context.py | PREPARE | B,Q,P; Späteres Tagesextrem verboten; overfit M; cost L |
| H37 Session-open behavior | ENTRY | Entry-Strata Open vs später, Regime/OR gleich | src/daxlab/research/session_context.py | PREPARE | B,Q,P; Kalender/Bar-Open-Close trennen; overfit M; cost L |
| H38 Lunch behavior | ENTRY | Entry-Strata Lunch, Regime/Struktur kontrolliert | src/daxlab/research/session_context.py | PREPARE | B,Q,P; Keine nachträglichen Lunch-Grenzen; overfit M; cost L |
| H39 Late-session behavior | ENTRY | Entry-Strata Late, verbleibende Sessionzeit | src/daxlab/research/session_context.py | PREPARE | B,Q,P; Keine zukünftige Close-Liquidität; overfit M; cost L |
| H40 M1 timing — later only | ENTRY | Erst stabiles M5-Regime/Structure; kausaler M1-Timinglayer | src/daxlab/research/entry_diagnostics.py | LATER | M1,Q,P; M5-Vollbar nicht vor Close bekannt; overfit H; cost M |

## Failure coverage

SYNTHETIC_ONLY means a referenced local test covers the documented subset, not every aspect of the trigger, not an IG adapter guarantee. A real Broker conformance drill is separate. MT5-specific instance/event-queue checks remain legacy-provider scope; they are not copied into an IG M01 gate.

| ID | Trigger | Owner | Unit subset | Status | Safe recovery |
| --- | --- | --- | --- | --- | --- |
| F001 | Alte Venue-Quote neu empfangen → scheinbar frisch | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Source-age UNKNOWN/block |
| F002 | Fehlende M5-Bar → Lücke | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Gap klassifizieren, kein erfundenes OHLC |
| F003 | Doppeltes Bar-Event → doppelte Decision | src/daxlab/adapters/ig_market_data.py | tests/test_candidate_operator_context.py::test_duplicate_bar_is_visible_as_yellow_runtime_event | SYNTHETIC_ONLY | Idempotent, kein neuer Attempt |
| F004 | Bars out of order → Feature springt | src/daxlab/adapters/ig_market_data.py | tests/test_candidate_operator_context.py::test_out_of_order_bar_is_visible_as_red_runtime_event | SYNTHETIC_ONLY | Reject/reorder nur klarer Replay-Scope |
| F005 | High<Low/OHLC außerhalb → falscher ATR | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Data block |
| F006 | Maxbars zu klein → historischer Ausschnitt fehlt | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | WAITING_EXTERNAL | Coverage UNKNOWN |
| F007 | Mid-Bar als CLOSED-M5 → Future-Info | src/daxlab/adapters/ig_market_data.py | tests/test_candidate_operator_context.py::test_unsafe_bar_is_visible_as_red_runtime_event | SYNTHETIC_ONLY | Decision nicht auf open bar |
| F008 | Corporate/data revision → Backtestabweichung | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Revision getrennt reporten |
| F009 | Bid/ask/mid verwechselt → Kostenedge | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Parity UNKNOWN, keine Cost-Promotion |
| F010 | Indikator-Warmup zu kurz → andere Signale | src/daxlab/adapters/ig_market_data.py | NOT_PROVEN | GAP | Warmup readiness block |
| F011 | UTC als Broker-Wallclock interpretiert → Offset | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | WAITING_EXTERNAL | Unresolved clock block |
| F012 | DST falsch → falscher Session-Open | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | Session UNKNOWN |
| F013 | Wallclock rückwärts → negative Duration | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | Invalidate clock evidence |
| F014 | NTP nicht synchron → Host/Broker drift | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | WAITING_EXTERNAL | Keine erfundene Toleranz |
| F015 | Scheduled task vor neuem Bar → stale Price | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | Stale source reject |
| F016 | Snapshot generated_at = fetch time → falsche Age | scripts/run_ig_raw_truth_2233.py | tests/test_operator_console_projection.py::test_fetch_time_cannot_renew_source_age_and_reuses_source_feed_limit | SYNTHETIC_ONLY | UNKNOWN/STale anzeigen |
| F017 | Tick/Bar Zeitsemantik gemischt → falscher Close | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | Keine silent normalization |
| F018 | Spätere Publikation rückdatiert → News Leakage | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | Beobachtungszeit maßgeblich |
| F019 | Replay nutzt live time → Locks re-armed | scripts/run_ig_raw_truth_2233.py | NOT_PROVEN | GAP | State replay isolieren |
| F020 | Broker reconnect, Daten verloren → connected aber stale | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Re-observe/resubscribe + reconcile |
| F021 | Public Feed lebt, Private Stream tot → keine Fills | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Inventory/recon UNKNOWN |
| F022 | Auto-discovery falsches Terminal → anderer Kontext | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | WAITING_EXTERNAL | Identity block |
| F023 | Account vor/nach Query geändert → mixed envelope | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Bundle contradiction |
| F024 | Orders query None → fälschlich flat | src/daxlab/runtime/candidate_operator_query.py | tests/test_demo_transport_query.py::test_missing_unknown_or_contradictory_venue_truth_never_allows_retry | SYNTHETIC_ONLY | QUERY_REQUIRED |
| F025 | History nur kurzer Zeitraum → Outcome fehlt | src/daxlab/runtime/candidate_operator_query.py | tests/test_operator_console_reconciliation.py::test_short_history_and_empty_inventory_never_assume_flat | SYNTHETIC_ONLY | UNKNOWN, kein Release |
| F026 | Trade/Fill vor History → temporärer Widerspruch | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Bounded grace, kein retry |
| F027 | Tick value/lot contract geändert → sizing falsch | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Neue Review/Admission block |
| F028 | Market closed/maintenance → feed scheinbar tot | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Closed vs unhealthy getrennt |
| F029 | API-Version unsupported → Mappingfehler | src/daxlab/runtime/candidate_operator_query.py | NOT_PROVEN | GAP | Unsupported block |
| F030 | Disconnect nach Transport vor ACK → unknown | src/daxlab/runtime/demo_transport_attempt_reservation.py | tests/test_demo_transport_restart.py::test_restart_preserves_exact_original_evidence_without_build_or_save | SYNTHETIC_ONLY | QUERY, nie resubmit |
| F031 | Request timeout → Outcome unklar | src/daxlab/runtime/demo_transport_attempt_reservation.py | tests/test_demo_transport_query.py::test_missing_unknown_or_contradictory_venue_truth_never_allows_retry | SYNTHETIC_ONLY | UNKNOWN; bounded query |
| F032 | Reconnect nur Preisabos → private state fehlt | src/daxlab/runtime/demo_transport_attempt_reservation.py | NOT_PROVEN | GAP | Broker truth UNKNOWN |
| F033 | Duplicate sessions → EOF/disconnect | src/daxlab/runtime/demo_transport_attempt_reservation.py | NOT_PROVEN | GAP | Stop new admission, inspect owner |
| F034 | Reporting channel down, transport up → blinder Betrieb | src/daxlab/runtime/demo_transport_attempt_reservation.py | NOT_PROVEN | GAP | Continuous execution block |
| F035 | Resend außerhalb retained window → verlorene Reports | src/daxlab/runtime/demo_transport_attempt_reservation.py | NOT_PROVEN | GAP | Incomplete evidence/query escalation |
| F036 | Offene Order beim Start → untracked exposure | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_inventory.py::test_account_wide_manual_inventory_visible_without_local_state_mutation | SYNTHETIC_ONLY | Inventory review block |
| F037 | Manuelle Order → ownership unknown | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_inventory.py::test_account_wide_manual_inventory_visible_without_local_state_mutation | SYNTHETIC_ONLY | Sichtbar, kein Auto-Cancel |
| F038 | Doppelter Report → Qty zweimal addiert | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Exactly-once state application |
| F039 | Status out of order → terminal zurück aktiv | src/daxlab/runtime/broker_reconciliation.py | tests/test_broker_order_lifecycle.py::test_event_time_cannot_move_backwards | SYNTHETIC_ONLY | Contradiction/query |
| F040 | Partial fill → „voll gefüllt“ | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_reconciliation.py::test_reconnect_fill_observed_but_unapplied_local_checkpoint_is_contradiction | SYNTHETIC_ONLY | Unapplied difference blocks |
| F041 | Pending cancel während Fill → Fill ignoriert | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Fill evidencen, outcome query |
| F042 | Replace rejected → alte Order vergessen | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Original state erhalten |
| F043 | Order History da, Deal fehlt → falsa Fillproof | src/daxlab/runtime/broker_reconciliation.py | tests/test_demo_transport_query.py::test_missing_unknown_or_contradictory_venue_truth_never_allows_retry | SYNTHETIC_ONLY | UNKNOWN, nicht fabricate Fill |
| F044 | Open Orders leer, Deal da → falsch notsubmitted | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_reconciliation.py::test_reconnect_fill_observed_but_unapplied_local_checkpoint_is_contradiction | SYNTHETIC_ONLY | Reconcile observed fill |
| F045 | Leerer Einzelreport als Terminalbeweis → Slot frei | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_reconciliation.py::test_short_history_and_empty_inventory_never_assume_flat | SYNTHETIC_ONLY | Reject inference |
| F046 | Duplicate Intent ID/ID-Regress → Order abgewiesen | src/daxlab/runtime/broker_reconciliation.py | tests/test_demo_transport_attempt_reservation.py::test_exact_replay_returns_original_without_second_save | SYNTHETIC_ONLY | Block/query, keine neue ID |
| F047 | Stop-limit Gap → keine Absicherungsausführung | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Non-fill risk klar zeigen |
| F048 | Venue Stop manuell entfernt → restart crash | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Incident/query, kein DB delete |
| F049 | Fehlende Order amount als 0 → Fill verloren | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Reject malformed, preserve evidence |
| F050 | Native Orderpreis digits-valid, tick-invalid | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Precision block |
| F051 | MQL Handler überläuft → Events verloren | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Query authoritative state |
| F052 | Position bereits bei Startup → Bot glaubt flat | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_inventory.py::test_account_wide_manual_inventory_visible_without_local_state_mutation | SYNTHETIC_ONLY | Review/block |
| F053 | Fremde Position → local journal leer | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_inventory.py::test_account_wide_manual_inventory_visible_without_local_state_mutation | SYNTHETIC_ONLY | Origin unknown, keine Aktion |
| F054 | Reconnect Fill fehlt lokal → Qty mismatch | src/daxlab/runtime/broker_reconciliation.py | tests/test_operator_console_reconciliation.py::test_reconnect_fill_observed_but_unapplied_local_checkpoint_is_contradiction | SYNTHETIC_ONLY | Reconcile/query; no retry |
| F055 | Netting aggregiert Orders → falsche Einzelposition | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Semantik block bei unbekannt |
| F056 | Hedging mehrere Positionen → eine überschrieben | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | ID-bound inventory |
| F057 | Average Price off native grid → falsche Contradiction | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | Preisarten unterscheiden |
| F058 | Reconciliation synthetischer Fill → „realer“ P&L | src/daxlab/runtime/broker_reconciliation.py | tests/test_nextgen_broker_lifecycle_conformance.py::test_matching_synthetic_venue_truth_reconciles_consistently | SYNTHETIC_ONLY | Nicht zu Brokertruth promoten |
| F059 | Trade bust/correction → alte Equity bleibt | src/daxlab/runtime/broker_reconciliation.py | NOT_PROVEN | GAP | History behalten, reclassify |
| F060 | LIVE statt DEMO → falsche Modeanzeige | src/daxlab/domain/risk_policy.py | NOT_PROVEN | WAITING_EXTERNAL | Hard block |
| F061 | Server falsch trotz gleicher Symbolnamen | src/daxlab/domain/risk_policy.py | NOT_PROVEN | WAITING_EXTERNAL | Context mismatch block |
| F062 | Unrealized P&L fehlt → Null angenommen | src/daxlab/domain/risk_policy.py | NOT_PROVEN | WAITING_EXTERNAL | Loss/exposure UNKNOWN |
| F063 | Ein-/Auszahlung → scheinbarer DD/Profit | src/daxlab/domain/risk_policy.py | NOT_PROVEN | GAP | Equity/strategy P&L trennen |
| F064 | Account Exposure nicht in Routerlimits → Überexposure | src/daxlab/domain/risk_policy.py | NOT_PROVEN | GAP | Aggregate controls before transport |
| F065 | Crash vor durable reservation → duplicate risk | src/daxlab/runtime/recovery_bundle.py | tests/test_demo_transport_restart.py::test_crash_at_reservation_write_never_triggers_transport | SYNTHETIC_ONLY | Durable-before-transport barrier |
| F066 | ACK commit noch nicht durable → nach Crash fehlt | src/daxlab/runtime/recovery_bundle.py | NOT_PROVEN | GAP | Unresolved query, no resubmit |
| F067 | Checkpoint beschädigt → default flat | src/daxlab/runtime/recovery_bundle.py | tests/test_candidate_state.py::test_tampered_state_fails_closed | SYNTHETIC_ONLY | Fail closed |
| F068 | DB down, console alive → fehlende current truth | src/daxlab/runtime/recovery_bundle.py | tests/test_operator_console_http.py::test_source_exception_and_credentials_are_never_sent_to_browser | SYNTHETIC_ONLY | UNKNOWN, no cached GREEN |
| F069 | Replay doppelt → Lifecycle doppelt angewendet | src/daxlab/runtime/recovery_bundle.py | NOT_PROVEN | GAP | Idempotent replay |
| F070 | Backup ungeprüft → Restore verliert Schema/State | src/daxlab/runtime/recovery_bundle.py | NOT_PROVEN | GAP | Keine Wiederaufnahme vor reconcile |
| F071 | Reset SeqNum/Store → unresolved vergessen | src/daxlab/runtime/recovery_bundle.py | NOT_PROVEN | GAP | Business evidence erhalten |
| F072 | Candidate hung, MT5 lebt → stale decisions | src/daxlab/runtime/mt5_watchdog.py | tests/test_operator_console_projection.py::test_candidate_behind_feed_is_stale_without_inventing_seconds_threshold | SYNTHETIC_ONLY | Candidate UNKNOWN/stale |
| F073 | Runtime lebt, MT5 tot → heartbeat GREEN | src/daxlab/runtime/mt5_watchdog.py | tests/test_operator_console_projection.py::test_alive_web_or_candidate_cannot_hide_down_host_mt5_or_clock | SYNTHETIC_ONLY | Readiness block, liveness separat |
| F074 | Web läuft, runtime tot → stale cached truth | src/daxlab/runtime/mt5_watchdog.py | tests/test_operator_console_dom.py::test_actual_js_renders_inventory_stale_unknown_and_clears_unreachable_endpoint | SYNTHETIC_ONLY | Stale/unknown prominently |
| F075 | Crash loop nach unresolved state → repeated starts | src/daxlab/runtime/mt5_watchdog.py | NOT_PROVEN | GAP | Backoff/escalate, keine Rearm |
| F076 | Falsche venv/cwd → andere Config/Dependencies | src/daxlab/runtime/mt5_watchdog.py | NOT_PROVEN | GAP | Build/context block |
| F077 | Prozess stirbt mit working Order → unowned risk | src/daxlab/runtime/mt5_watchdog.py | NOT_PROVEN | WAITING_EXTERNAL | Operator recovery; no auto action |
| F078 | Lange grid mirror logic → Updates verpasst | src/daxlab/runtime/mt5_watchdog.py | NOT_PROVEN | GAP | Bound work, semantic health |
| F079 | Sessionlogs bei Restart überschrieben → Incident verloren | src/daxlab/runtime/mt5_watchdog.py | NOT_PROVEN | GAP | Existing journal retain |
| F080 | Symbolalias falsch → anderer Kontrakt | src/daxlab/runtime/broker_economics_readiness.py | tests/test_demo_transport_attempt_reservation.py::test_same_bundle_symbol_cross_wiring_blocks | SYNTHETIC_ONLY | Mismatch block |
| F081 | Wrong server defaults aus initialize | src/daxlab/runtime/broker_economics_readiness.py | NOT_PROVEN | WAITING_EXTERNAL | No implicit account promotion |
| F082 | Fixed-Fraction Research als Cash Policy → sizing drift | src/daxlab/runtime/broker_economics_readiness.py | NOT_PROVEN | GAP | Policy UNKNOWN, no substitution |
| F083 | API verb setzt/modifiziert gleichermaßen → accidental modify | src/daxlab/runtime/broker_economics_readiness.py | NOT_PROVEN | GAP | Separate authorized control paths |
| F084 | Docker/public bind → Console exponiert | src/daxlab/runtime/broker_economics_readiness.py | tests/test_operator_console_http.py::test_dns_rebinding_or_cross_origin_cannot_read_runtime | SYNTHETIC_ONLY | Localhost/VPN, kein public API |
| F085 | Caller limit ungeprüft als kanonisch → falsche Freshness | src/daxlab/runtime/broker_economics_readiness.py | tests/test_operator_console_matrices.py::test_fetch_never_substitutes_for_evidence_or_invents_threshold | SYNTHETIC_ONLY | UNVERIFIED_THRESHOLD |
| F086 | Uneinheitliches Deployment → alter Router aktiv | src/daxlab/runtime/manifests.py | NOT_PROVEN | GAP | Deployment block |
| F087 | Code SHA gleich, Config anders → falsche Evidence | src/daxlab/runtime/manifests.py | tests/test_candidate_shadow_checkpoint.py::test_checkpoint_rejects_different_run_manifest | SYNTHETIC_ONLY | Bundle mismatch block |
| F088 | Schema downgrade unvereinbar → State verloren | src/daxlab/runtime/manifests.py | NOT_PROVEN | GAP | Stop, retain state |
| F089 | Rollback löscht consumed Slot → duplicate admission | src/daxlab/runtime/manifests.py | NOT_PROVEN | GAP | No state reset |
| F090 | Changed precision/reconnect ohne Conformance → hidden drift | src/daxlab/runtime/manifests.py | NOT_PROVEN | GAP | Specific environment review |
| F091 | GitHub unavailable → unbekannter Deploy-Head | src/daxlab/runtime/manifests.py | NOT_PROVEN | GAP | Keine neue Promotion |
| F092 | Execution GREEN trotz NONE/false → falsche Freigabe | src/daxlab/runtime/operator_runtime_bridge.py | tests/test_operator_console_execution.py::test_actual_http_response_rejects_contradictory_projection | SYNTHETIC_ONLY | DISABLED/BLOCKED |
| F093 | Heartbeat verschluckt Blocker → Readiness falsch | src/daxlab/runtime/operator_runtime_bridge.py | tests/test_operator_console_heartbeat.py::test_green_heartbeat_preserves_blocker_and_keeps_independent_liveness | SYNTHETIC_ONLY | Liveness≠Readiness |
| F094 | Best parameter nach vielen Trials → overfit | src/daxlab/research/multiple_testing_preflight.py | tests/test_multiple_testing_preflight.py::test_rejected_abandoned_failed_trials_are_not_filtered | SYNTHETIC_ONLY | Exploratory, no promotion |
| F095 | Unlimited averaging/rescue → Exposure eskaliert | src/daxlab/runtime/operator_runtime_bridge.py | NOT_PROVEN | GAP | REJECT strategy pattern |
| F096 | Operator ACK released unknown slot → duplicate risk | src/daxlab/runtime/demo_transport_attempt_reservation.py | NOT_PROVEN | GAP | Query/block remains |
| F097 | Fehleremails ohne Action → Incident eskaliert | src/daxlab/runtime/operator_runtime_bridge.py | NOT_PROVEN | GAP | Benannter Operator/triage |
| F098 | Secret in logs/screenshots/JSON → Leakage | src/daxlab/runtime/operator_runtime_bridge.py | tests/test_operator_console_credentials.py::test_secret_strings_never_reach_actual_http_response | SYNTHETIC_ONLY | Fail-closed projection, secure rotation |
| F099 | Static Research als current Host → falsches Vertrauen | src/daxlab/runtime/operator_runtime_bridge.py | tests/test_operator_console_projection.py::test_console_does_not_equate_strategy_or_local_shadow_green_with_broker_readiness | SYNTHETIC_ONLY | Sichtbar getrennt |
| F100 | UNKNOWN als GREEN gelesen → Freigabefehler | src/daxlab/runtime/operator_runtime_bridge.py | tests/test_operator_console_dom.py::test_actual_js_renders_inventory_stale_unknown_and_clears_unreachable_endpoint | SYNTHETIC_ONLY | Keine implicit OK, Runbook |

## Architecture learnings

| ID | Learning | Decision | Owner | Evidence |
| --- | --- | --- | --- | --- |
| L01 | Broker-Wahrheit und lokalen Intent nicht verschmelzen — ALREADY_HAVE. | ALREADY_HAVE | src/daxlab/runtime/broker_reconciliation.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L02 | Verbindungsstatus nicht als State-Synchronität verwenden — EXTEND evidence, S33. | EXTEND | src/daxlab/runtime/mt5_watchdog.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L03 | Restore vor neuer Execution — EXTEND composition, S01/S04. | EXTEND | src/daxlab/runtime/restart_reconcile.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L04 | Vollaccount-Inventar statt nur bekannte Tickets — ALREADY_HAVE; S27/S28. | ALREADY_HAVE | src/daxlab/runtime/candidate_operator_query.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L05 | Error, empty, unavailable und bounded missing unterscheiden — ALREADY_HAVE. | ALREADY_HAVE | src/daxlab/runtime/broker_reconciliation.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L06 | Unknown Transport bleibt QUERY, niemals Retry — ALREADY_HAVE. | ALREADY_HAVE | src/daxlab/runtime/demo_transport_attempt_reservation.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L07 | Partial/Cumulative/Last Quantity getrennt — EXTEND real Conformance, S12/S32. | EXTEND | src/daxlab/runtime/broker_order_lifecycle.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L08 | Report-Idempotenz ist Business-Semantik, nicht nur Transportsequence — EXTEND tests, S31. | EXTEND | src/daxlab/runtime/broker_execution_telemetry_journal.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L09 | Ownership nicht aus einem Kommentar erraten — EXTEND, S01. | EXTEND | src/daxlab/runtime/broker_order_lifecycle.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L10 | Reconnect resubscribe und inventory reconcile separat — EXTEND, S33. | EXTEND | src/daxlab/runtime/restart_reconcile.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L11 | Risk admission unabhängig von Signal — EXTEND PTC, S35/S36. | EXTEND | src/daxlab/domain/risk_policy.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L12 | Out-of-band Authority kann nicht vom Strategy-Prozess aufgehoben werden — RESEARCH, S37. | EXTEND | src/daxlab/runtime/broker_execution_protection.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L13 | Observation Plane bleibt credential-free/read-only — ALREADY_HAVE, S07/S48. | ALREADY_HAVE | src/daxlab/runtime/candidate_operator_telemetry.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L14 | Snapshot/Freshness-Zeiten nicht substituieren — ALREADY_HAVE/EXTEND source evidence. | ALREADY_HAVE | src/daxlab/runtime/candidate_operator_query.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L15 | Event- und Receive-Zeit plus monotonic Dauer unterscheiden — EXTEND. | EXTEND | src/daxlab/runtime/broker_order_lifecycle.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L16 | Replay erzeugt keine neuen IDs/Transporte — EXTEND negative contracts. | EXTEND | src/daxlab/runtime/candidate_publication_state.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L17 | Atomic/durable-before-transport Evidence separat beweisen — EXTEND conformance, S50. | EXTEND | src/daxlab/runtime/demo_transport_attempt_reservation.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L18 | Release identity umfasst Policy/Config/Schema, nicht nur Code — EXTEND. | EXTEND | src/daxlab/runtime/manifests.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L19 | Rollback konserviert Reservations und Brokerstate — ALREADY_HAVE rule, EXTEND drill. | EXTEND | src/daxlab/runtime/recovery_bundle.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L20 | Health zeigt Ursachen, nicht Gesamt-GREEN — ALREADY_HAVE. | ALREADY_HAVE | src/daxlab/runtime/operator_runtime_bridge.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L21 | Simulation assumptions sind keine realen Fill-Facts — ALREADY_HAVE rule, S09/S12/S14. | ALREADY_HAVE | src/daxlab/research/conformance.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L22 | Günstiges kausales Screening vor teurer Validation — ALREADY_HAVE/EXTEND staged workflow. | EXTEND | src/daxlab/research/variant_trial_registry.py | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |
| L23 | Incident-Timeline zeigt tatsächliche Kenntniszeit; Snapshotzeit ist keine Transitionzeit — ALREADY_HAVE limit. | ALREADY_HAVE | src/daxlab/runtime/broker_execution_telemetry_journal.py | EXISTING_LOCAL_CONTRACT_REAL_BROKER_SCOPE_STILL_EXTERNAL |
| L24 | Mehr Architecture ohne zusätzliche Broker-/Risk-/Profit-Evidence ablehnen — REJECT. | REJECT | docs/WORK_CONTINUITY_PROTOCOL.md | SCENARIO_SPECIFIC_TEST_OR_IG_DEMO_CONFORMANCE |

## Research scheduling and M10 preparation

Cheap reject validates source identity, UTC/timeframe/session calendar, finalized-only eligibility, OHLC and chronology, ledger non-overlap, quote/volume validity and complete cost evidence. Feature-only prefix/warmup perturbation tests precede all outcome screening. Coarse regime H01–H12 first, then structure H15–H25, then entry H26–H39 within the declared strata. H13 needs true volume; H14 publish/revision provenance; H40 independent M1 parity. No strategy/config/engine mutation.

Each trial family uses existing variant_trial_registry.TrialDeclaration and chronology audit; new outcomes cannot retroactively become predeclared. Full provenance: hypothesis/dataset/engine/strategy/risk/cost/session/timezone/adapter/execution-assumptions/parameters/code/results. Coarse exploratory selection has a bounded declared trial budget; all rejected/failed/abandoned trials remain counted. Selected deep tests precede temporal OOS/WF; final holdout is preserved. DSR/PBO/SPA existing owners remain; synchronized complete return matrices are required. Plateaus, neighborhood gradients, count/cost sensitivity, top-trade dependency and WF/forward degradation are separate outputs; no magic optimum or automatic promotion.

There is no valid current CAND-001 pinned trade/path ledger in the repository tree. Targeted Library retrieval found research summaries/notebooks, not a proven cost/path-complete CAND-001 ledger. Real numerical envelope/tail/filter/OOS conclusions remain WAITING_EXTERNAL. Pure diagnostics can be extended offline with hand-calculated fixtures; these do not establish profitability.


## Subsequent acceleration coverage update

Current JSON:42 rows with narrow local references;53 GAP,38 SYNTHETIC_ONLY,9 WAITING_EXTERNAL. F033/F050 now SYNTHETIC_ONLY; source/reconnect/equity evidence gaps stay open. Original2234 rows above are historical mapping snapshots; use JSON for current classification.
