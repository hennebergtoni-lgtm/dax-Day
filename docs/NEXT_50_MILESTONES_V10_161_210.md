# V10 — Next 50 Milestones (161–210)

Status: IN PROGRESS — AUTHORIZED FOR NON-LIVE DEVELOPMENT
Date: 2026-09-09

User authorization covers the next 50 project steps. It authorizes continued offline engineering, synthetic SHADOW soak testing and PAPER preparation. It does **not** authorize LIVE real-money execution. Real MT5 host evidence remains mandatory for external milestones 102–110.

## 161–170 — V9 closeout and soak foundation
- [x] 161. Confirm final V9 PR #6 head CI #436 GREEN.
- [ ] 162. Merge CI-green V9 offline MT5-to-SHADOW integration. Deferred until V10 branch validation; V10 is based on the same CI-green V9 head.
- [x] 163. Create dedicated V10 offline soak branch from the CI-green V9 head.
- [x] 164. Freeze V10 scope: synthetic/offline only; no broker order API.
- [x] 165. Add deterministic multi-bar SHADOW soak runner.
- [x] 166. Require all soak outputs to remain `NO_ORDER`.
- [x] 167. Add deterministic per-bar decision IDs through the existing frozen-reference SHADOW decision contract.
- [x] 168. Add duplicate-bar/decision suppression across a soak run.
- [x] 169. Add run-level counters for processed / blocked / duplicate observations.
- [x] 170. Add deterministic run fingerprint over ordered decision IDs and checkpoint identity.

## 171–180 — Restart, resume and fault recovery
- [x] 171. Add soak checkpoint schema/version.
- [x] 172. Persist last accepted closed-bar identity in checkpoint state.
- [x] 173. Add resume from checkpoint without reprocessing accepted bars.
- [x] 174. Add explicit full-run vs split-run/resume final-checkpoint parity test.
- [x] 175. Add repeated-resume idempotency test.
- [x] 176. Add checkpoint tamper detection.
- [x] 177. Add simulated process interruption and clean recovery test.
- [x] 178. Add stale-feed fault injection during soak.
- [x] 179. Add missing-bar/discontinuity fault injection at the closed-M5 feed boundary.
- [x] 180. Add out-of-order/duplicate rejection at the closed-M5 feed boundary.

## 181–190 — Watchdog and safety matrix
- [x] 181. Add clock-unsafe fault injection.
- [x] 182. Add host-unhealthy/disconnected fault injection at the SHADOW observation boundary.
- [x] 183. Add account-disconnected fault injection through host evidence.
- [x] 184. Add engine-loop-unhealthy fault injection through host evidence.
- [x] 185. Add single-instance-lock loss fault injection.
- [x] 186. Add execution-flag-on negative test through the host-to-SHADOW bridge; SHADOW blocks.
- [x] 187. Add deterministic blocker ordering across simultaneous SHADOW observation faults.
- [x] 188. Add recovery-after-fault test without retroactive decisions.
- [ ] 189. Add aggregate watchdog health summary for a multi-bar soak run.
- [x] 190. Prove current soak/host safety faults cannot create an order-capable output.

## 191–200 — Decision-core and operator visibility
- [x] 191. Convert synthetic closed-M5 bars into canonical runtime `Candle` objects in bridge tests.
- [x] 192. Validate Berlin session normalization on synthetic winter data.
- [x] 193. Validate Berlin session normalization on synthetic summer data.
- [x] 194. Add DST-boundary soak fixture.
- [x] 195. Add deterministic V11.2 fixture replay alongside soak evidence.
- [x] 196. Compare repeated V11.2 fixture replay fingerprints.
- [x] 197. Add deterministic run-manifest identity test for synthetic SHADOW soak.
- [x] 198. Add credential-free iPhone-readable soak summary payload.
- [x] 199. Add soak status to web/read-only operator state without claiming broker evidence.
- [x] 200. Add explicit `SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE` marker to soak summary/recovery/web evidence.

## 201–210 — Paper preparation without starting Paper
- [x] 201. Define versioned `ExecutionIntent` contract separate from Decision Core.
- [x] 202. Define deterministic client/order identity contract.
- [x] 203. Add duplicate-intent rejection contract/test.
- [x] 204. Define paper lifecycle states ACK / REJECT / PARTIAL / FILLED / CANCELLED.
- [x] 205. Define versioned paper fill-model configuration contract.
- [x] 206. Add conservative spread/slippage/commission fields to paper model.
- [x] 207. Add same-bar stop/target ambiguity policy contract.
- [x] 208. Add gap-through and partial-fill policy contracts.
- [x] 209. Add paper telemetry/reconciliation schema with simulation-only capability and no broker credentials.
- [ ] 210. HARD REVIEW: Paper remains NOT STARTED; LIVE remains NOT AUTHORIZED; real MT5 host evidence and full readiness evidence are still required.

## Current boundary
- The synthetic SHADOW soak can process many deterministic M5 observations, checkpoint/resume, suppress duplicates and inject multiple safety faults while remaining `NO_ORDER`.
- Paper preparation now has versioned intent, lifecycle, fill-model and telemetry contracts, but no broker adapter and no order submission function.
- No synthetic evidence satisfies external MT5 milestones 102–110.
- All new V10 code remains PENDING CI until the V10 pull-request gate passes.

## Binding constraints
- V11.2 remains the immutable active reference.
- ATR001 and all other research families remain research objects unless separately promoted by evidence.
- Synthetic soak evidence never becomes broker evidence.
- No MT5 order API is added in this block.
- `order_execution_enabled=false` remains the prospective SHADOW/PAPER preparation default.
- LIVE requires a separate explicit authorization and later safety/readiness evidence.
