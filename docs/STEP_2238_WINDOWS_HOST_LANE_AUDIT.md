# Step2238 Windows host-lane audit

## Canonical Windows Python runtime selection — 2026-09-15

Code head `30d9575fc8b8526e281a86c9717d19e9dda6b71b` owns the selection
contract; the final documentation commit does not change its runtime blobs.
On that exact runtime head, `windows-host-lane-ci` #8, `dax-bot-1x-ci` #719 and
`research-lab-ci` #1503 are GREEN.

The latest real Windows run completed exact-head deployment and stopped before
authentication with `PYTHON_COMMAND_RESULT_MULTIPLE`, `failure_phase=PYTHON`,
`exception_class=OTHER` and `legacy_partial_state=NONE_DETECTED`. This proves a
resolver-cardinality block, not multiple usable interpreters. It produced no IG
login, broker query or order. Historical output is retained; the active owner no
longer treats multiple `Get-Command` rows as runtime ambiguity.

The canonical contract is now:

1. discover the configured `python`/`python.exe` family and the `py`/`py.exe -3`
   fallback without reading credentials;
2. normalize duplicate launcher paths and reject Microsoft WindowsApps Store
   aliases without starting them;
3. probe each remaining candidate in a separate stderr-suppressed process;
4. accept only CPython 3.11+, matching PowerShell process architecture, an
   absolute existing `sys.executable`, exact deployment-owned `daxlab` and
   collector origins, and unchanged `NONE/false` safety;
5. group resolver results by the sanitized runtime identity fingerprint;
6. select the only valid identity at the highest priority. The explicitly
   configured family is rank 0; `py -3` is a fallback. More than one distinct
   valid identity at the same best rank is `PYTHON_RUNTIME_AMBIGUOUS`; none is
   `PYTHON_RUNTIME_NO_VALID_CANDIDATE`.

Step2237 previously proved the host's default `python` command path functionally,
but did not record an executable pathname. Accordingly the repository does not
invent a hard-coded host path: it gives that proven command family priority and
re-proves full path, version, architecture and exact import origin on every
isolated deployment. The selected real `sys.executable`, not `py.exe`, starts
the 51-check preflight and eventual collector.

Native Windows failure injection covers: `python` plus `python.exe` resolving to
one interpreter, `python` plus `py` resolving to one interpreter, two different
valid same-rank interpreters, a WindowsApps alias, a duplicated PATH result, an
additional wrong-version interpreter, and exactly one valid interpreter among
multiple candidates. Shape/path/start anomalies remain sanitized. Any genuine
ambiguity prevents the 51-check preflight and therefore prevents IG login.

Status remains **IMPLEMENTED / WAITING_EXTERNAL** pending exactly one run on the
new immutable final head. M01 and the 27-gate tally remain unchanged at **8
VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED**. Effective safety
is `execution_capability=NONE`, `order_execution_enabled=false`; no order; LIVE
prohibited.

## Decision — 2026-09-15

Code head `6bf1a6bbbcc0af24ba35a6c8397a614f241013fe` replaces the
Step2238 one-error Python bootstrap with one reusable Windows host runtime owner
and an aggregate, credential-free preflight. The repository work is
**IMPLEMENTED**. Step2238 remains **WAITING_EXTERNAL** until this exact code plus
the documentation closeout head succeeds on the real Windows host. No IG login
or read is claimed by local/CI evidence.

Effective safety remains `execution_capability=NONE` and
`order_execution_enabled=false`. The lane contains no dealing endpoint, retry,
resubmit, slot release, state reset or evidence overwrite. LIVE is prohibited.

## Root-cause clusters

The historic failures are retained as evidence. Only failure *classes* supported
by code and real-run boundaries are grouped; an unobserved Windows leaf cause is
not invented.

| Cluster | Historic symptoms | Repository finding | Resolution |
| --- | --- | --- | --- |
| Mutable/shared deployment | `DETACHED_CHECKOUT_FAILED`, `WORKTREE_ADD_FAILED_DEPLOYMENT_RETAINED` | In-place detach and shared worktree administration coupled the run to the existing checkout. | The Step2237-proven short-path isolated local clone remains the deployment owner. |
| Bootstrap boundary | `BOOTSTRAP_DOWNLOAD_OR_START_FAILED` | A pre-deployment download/start path added a second failure surface. | Exact-head source comes from the gated local repository; no separate payload download occurs after START. |
| Python/PowerShell impedance | `PYTHON_START_FAILED`, `RUNNER_UNEXPECTED_FAILURE` | `-I -S`, `runpy`, repeated JSON probes and PowerShell scalar/array coercion created more boundaries than the read-only payload needs. | Direct exact-clone script execution is restored; one PowerShell module owns discovery/process/output semantics. |
| Contract drift inside the lane | Would have caused deterministic false blocks | Step2238 preflight used `IG_IDENTIFIER` although the proven credential owner uses `IG_USERNAME`; it also expected the isolated clone's origin to be GitHub although a local clone correctly points to the source checkout. | One shared credential-shape owner is used by preflight and collector; source-origin and local-deployment-origin contracts are separated and tested. |
| First-error diagnostics | Generic or single leaf output | Independent local checks stopped before revealing adjacent defects. | 51 safe checks aggregate before authentication and publish a sanitized matrix. |
| Evidence publication | Partial directory could look complete | Direct writes did not provide a publication boundary/readback proof. | Both preflight and Step2238 bundles use exclusive staging, hashes, readback and atomic publication; only runner-owned staging may be removed. |

Step2237 already proves that this Windows host can perform the isolated clone,
direct Python start, exact-head imports, one IG read-only session and controlled
cleanup. Step2238 adds account, inventory bracket, market v4/economics, bounded
history and the aggregate host/network/credential-shape preflight. The host is
therefore not classified as unsuitable.

## Architecture disposition

| Component | Decision | Canonical owner / reason |
| --- | --- | --- |
| Exact-head drift gate and isolated local clone | KEEP | `run_ig_predemo_readiness_2238.ps1`; real-proven Step2237 pattern, existing checkout untouched. |
| Ownership-token cleanup | KEEP | Only the short, marker-bound, non-reparse deployment created by this invocation may be deleted. |
| One authenticated read-only session | KEEP | `IgDemoReadOnlyClient`; no automatic relogin and no dealing method. |
| `-I -S` plus `runpy` collector bootstrap | REMOVE | It obstructed exact project imports and duplicated runtime probing. Isolated mode remains a capability check, not a payload requirement. |
| Step-specific Python PowerShell owner | MERGE | Replaced by `dax_windows_host_lane.psm1`, reusable by later step payloads. |
| Local/Network/Credential preflight | REPLACE | `dax_windows_host_preflight.py` aggregates independent checks and emits one JSON contract. |
| Credential key parsing | MERGE | `ig_demo_credential_contract.py` is shared by preflight and existing probe/collector. |
| Collector evidence writes | SIMPLIFY | One staging/readback/publication path; no second evidence store. |
| Old `ig_predemo_python_runtime.psm1` and its step-specific injection script | REMOVE | Superseded files are deleted; their git history remains historical evidence. |

## Phase contract

| Phase | Permitted work | Fail-closed result |
| --- | --- | --- |
| A — Local preflight | Host, PowerShell, Git provenance, filesystem, Python, import origin, namespace, credential presence/shape. Credential values are neither printed nor persisted. | Full safe matrix is emitted; no IG login. |
| B — Network preflight | Credential-free DNS, TLS and HTTPS-stack reachability for GitHub and IG DEMO; proxy variable names only. | Full safe matrix is emitted; no IG login. |
| C — Authenticated read-only | Only after all required A/B checks pass: one login, accounts, bracketed positions/orders, market v4, bounded activity, M5, one logout. | No retry; transport/auth/read uncertainty is terminal for the run. |
| D — Evidence validation | Stage, hash, manifest, readback, atomic publish and ownership-bound deployment cleanup. | Existing evidence is retained; no overwrite or silent repair. |

The PowerShell operator output is `START`, then a 51-row `PREFLIGHT_ITEM`
matrix and aggregate counts, then either a fail-closed `SUMMARY` or
`AUTH READ-ONLY START` followed by the final `SUMMARY`. Raw stderr is never
forwarded. Sanitized details are limited to fixed reason codes, allow-listed
exception class, version/edition, architecture, executable basename/hash,
module-origin result, protocol/status class and path category.

## Preflight matrix

| Dimension | Checks | Count | Authentication permitted on failure? |
| --- | --- | ---: | --- |
| HOST | Windows identity, architecture, locale, timezone, broad UTC sanity, TEMP root, TEMP create/read/write/delete | 7 | No |
| POWERSHELL | version/edition, executable basename, FullLanguage, process architecture | 4 | No |
| GIT | executable/version, source-bound origin, exact head, proven clone/checkout/long-path/hooks isolation | 8 | No |
| FILESYSTEM | runtime root, reparse veto, UTF-8 readback, atomic replace, long path, cleanup | 6 | No |
| PYTHON | 3.11+, architecture, host parity, executable identity, stdlib, isolated-mode capability, no third-party requirement | 7 | No |
| IMPORT | collector compile, daxlab import/origin, collector import/origin | 5 | No |
| NETWORK | GitHub and IG DNS/TLS/HTTPS plus non-blocking proxy observation | 7 | No |
| CREDENTIAL | file, UTF-8 and exact shared three-key shape | 3 | No |
| EVIDENCE | safe namespace, exclusivity, strict UTF-8 JSON | 3 | No |
| SAFETY | static NONE/false/no-dealing contract | 1 | No |
| **Total** |  | **51** |  |

Independent safe failures aggregate as `PASS`, `FAIL`, `BLOCKED`, `UNKNOWN` or
`NOT_REQUIRED`. Required checks accept only PASS or an explicit NOT_REQUIRED;
optional observations do not affect sufficiency. A proxy observation is optional UNKNOWN and never exposes its
value. `RUNNER_UNEXPECTED_FAILURE` remains only a final safety net; all audited
operations map to HOST, POWERSHELL, GIT, FILESYSTEM, PYTHON, IMPORT, NETWORK,
CREDENTIAL, IG_SESSION/IG_READ, EVIDENCE or CLEANUP codes.

## Failure injection and system reaction

The machine-checked register maps 38 required scenarios, including multiple or
missing Python commands, wrong version/architecture, path and import-origin
failures, module shadowing, collector output/JSON/exit anomalies, unavailable or
read-only runtime, existing namespace, Git failures, long paths, cleanup denial,
DNS/TLS/proxy failures, malformed credentials, abnormal clock and partial or
mismatched publication. Native PowerShell tests exercise scalar/array/null and
.NET exception behavior. Python tests exercise aggregation, credential secrecy,
network classification, paths with spaces/non-ASCII characters and exclusive
evidence publication.

System reaction remains invariant:

- HOST, POWERSHELL, GIT, FILESYSTEM, PYTHON, IMPORT, NETWORK or CREDENTIAL block
  means no IG login;
- broker/inventory/economics UNKNOWN means no Step2239 admission;
- PTC or lifecycle uncertainty means no execution intent;
- partial/unknown transport remains QUERY_REQUIRED with no resubmit or slot
  release.

## Windows CI and Linux requirement

`windows-host-lane-ci` runs on `windows-latest` and validates PowerShell parsing,
native failure injection, Windows path/import/output behavior, Python tests,
Ruff and syntax. This is parity evidence, not user-host evidence.

**Linux worker: NOT_REQUIRED.** The real runtime target is Windows, the payload
uses the Python standard library, and neither Step2238 nor the IG read-only
client requires a Linux process. Linux CI remains useful for platform-neutral
regressions only; no Linux infrastructure is introduced.

## Automatic evidence transfer

Status: **PARTIAL**. The runner automatically validates, sanitizes, hashes,
manifests and publishes both the diagnostic preflight and successful readiness
bundle under the existing host runtime root. The complete sanitized preflight
matrix is also present in console output, so a failed run no longer needs a
manual diagnostic chain or ZIP handoff. Automatic remote upload is a **GAP**:
there is no repository-owned, host-configured authenticated upload channel whose
destination, retention and write authority are proven. Neon or a new service is
not assumed. The local evidence store remains canonical until such a channel is
separately authorized and configured.

## Current readiness state

No new real-host bundle exists for this code head, so status does not advance:

| Status | Gates | Count |
| --- | --- | ---: |
| VERIFIED | 1, 2, 4, 5, 6, 23, 24, 27 | 8 |
| IMPLEMENTED | — | 0 |
| WAITING_EXTERNAL | 3, 7–18 | 13 |
| BLOCKED | 19–22, 25, 26 | 6 |

Step2238 is **IMPLEMENTED / WAITING_EXTERNAL**. Step2239 is **IMPLEMENTED /
WAITING_EXTERNAL** because real native economics, inventory and session values
are not yet available. Step2240 remains **IN_PROGRESS / BLOCKED**; repository
UNKNOWN/partial/restart rules exist, but native IG reservation,
submit/confirm/query and real reconciliation/protection evidence do not. M01 is
**IN_PROGRESS** and DEMO readiness is **NOT READY**.

Exactly one real Windows invocation is the next action. A successful exact-head
run is then reviewed in the same work context for Step2238 acceptance and
Step2239 binding. No second runner or manual diagnostic command is currently
justified.
