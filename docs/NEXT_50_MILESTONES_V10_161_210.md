# V10 — Next 50 Milestones (161–210)

Status: AUTHORIZED FOR NON-LIVE DEVELOPMENT
Date: 2026-09-09

User authorization covers the next 50 project steps. It authorizes continued offline engineering, synthetic SHADOW soak testing and PAPER preparation. It does **not** authorize LIVE real-money execution. Real MT5 host evidence remains mandatory for external milestones 102–110.

## 161–170 — V9 closeout and soak foundation
- [x] 161. Confirm final V9 PR #6 head CI #436 GREEN.
- [ ] 162. Merge CI-green V9 offline MT5-to-SHADOW integration.
- [x] 163. Create dedicated V10 offline soak branch from the CI-green V9 head.
- [x] 164. Freeze V10 scope: synthetic/offline only; no broker order API.
- [ ] 165. Add deterministic multi-bar SHADOW soak runner.
- [ ] 166. Require all soak outputs to remain `NO_ORDER`.
- [ ] 167. Add deterministic per-bar decision IDs.
- [ ] 168. Add duplicate-bar suppression across a soak run.
- [ ] 169. Add run-level counters for processed / blocked / duplicate observations.
- [ ] 170. Add run fingerprint over ordered decision IDs.

## 171–180 — Restart, resume and fault recovery
- [ ] 171. Add soak checkpoint schema/version.
- [ ] 172. Persist last accepted closed-bar identity in checkpoint state.
- [ ] 173. Add resume from checkpoint without reprocessing accepted bars.
- [ ] 174. Add full-run vs split-run/resume parity test.
- [ ] 175. Add repeated-resume idempotency test.
- [ ] 176. Add checkpoint tamper detection.
- [ ] 177. Add simulated process interruption and clean recovery test.
- [ ] 178. Add stale-feed fault injection during soak.
- [ ] 179. Add missing-bar/discontinuity fault injection during soak.
- [ ] 180. Add out-of-order/duplicate fault injection during soak.

## 181–190 — Watchdog and safety matrix
- [ ] 181. Add clock-unsafe fault injection.
- [ ] 182. Add host-disconnected fault injection.
- [ ] 183. Add account-disconnected fault injection.
- [ ] 184. Add engine-heartbeat-unhealthy fault injection.
- [ ] 185. Add single-instance-lock loss fault injection.
- [ ] 186. Add execution-flag-on negative test; SHADOW must block.
- [ ] 187. Add deterministic blocker ordering across simultaneous faults.
- [ ] 188. Add recovery-after-fault test without retroactive decisions.
- [ ] 189. Add watchdog health summary for a soak run.
- [ ] 190. Prove no safety fault can create an order-capable output.

## 191–200 — Decision-core and operator visibility
- [ ] 191. Convert synthetic closed-M5 bars into canonical runtime `Candle` objects.
- [ ] 192. Validate Berlin session normalization on synthetic winter data.
- [ ] 193. Validate Berlin session normalization on synthetic summer data.
- [ ] 194. Add DST-boundary soak fixture.
- [ ] 195. Add deterministic V11.2 fixture replay alongside soak evidence.
- [ ] 196. Compare repeated V11.2 fixture replay fingerprints.
- [ ] 197. Add run manifest identity for synthetic SHADOW soak.
- [ ] 198. Add credential-free iPhone-readable soak summary.
- [ ] 199. Add soak status to web/read-only operator state without claiming broker evidence.
- [ ] 200. Add explicit `SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE` marker to all soak evidence.

## 201–210 — Paper preparation without starting Paper
- [ ] 201. Define versioned `ExecutionIntent` contract separate from Decision Core.
- [ ] 202. Define deterministic client/order identity contract.
- [ ] 203. Add duplicate-intent rejection contract/test.
- [ ] 204. Define paper lifecycle states ACK / REJECT / PARTIAL / FILLED / CANCELLED.
- [ ] 205. Define versioned paper fill-model configuration contract.
- [ ] 206. Add conservative spread/slippage/commission fields to paper model.
- [ ] 207. Add same-bar stop/target ambiguity policy contract.
- [ ] 208. Add gap-through and partial-fill policy contracts.
- [ ] 209. Add paper telemetry/reconciliation schema with no broker credentials.
- [ ] 210. HARD REVIEW: Paper remains NOT STARTED; LIVE remains NOT AUTHORIZED; real MT5 host evidence and full readiness evidence are still required.

## Binding constraints
- V11.2 remains the immutable active reference.
- ATR001 and all other research families remain research objects unless separately promoted by evidence.
- Synthetic soak evidence never becomes broker evidence.
- No MT5 order API is added in this block.
- `order_execution_enabled=false` remains the prospective SHADOW/PAPER preparation default.
- LIVE requires a separate explicit authorization and later safety/readiness evidence.
