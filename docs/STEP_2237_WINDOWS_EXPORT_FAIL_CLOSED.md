# Step2237 Windows export fail-closed audit

## Observed

Runner head ef24d63470b2d2ec076089d7ee8a39d0dbcae2ec reached START but not WAIT, then generic BLOCKED/FAIL_CLOSED and outer RUNNER_FAILED. No ZIP. Originals retained; no login/broker call.

## Proven repository cause

The failure occurred before Python, within remote/worktree/head/ancestry/fetch/checkout gates. The old PowerShell owner collapsed every Git failure into GIT_GATE_FAILED and its outer catch discarded even that code. The exact underlying external gate cannot be reconstructed from the supplied generic output. Selecting one would be fabrication. The proven repository defect is loss of causal error identity.

## Fixed error taxonomy

| Phase | Fixed credential-free codes |
| --- | --- |
| Input/host | HEAD_INVALID, HOST_UNAVAILABLE, GIT_NOT_AVAILABLE |
| Origin/worktree | REMOTE_QUERY_FAILED, REMOTE_MISMATCH, WORKTREE_STATUS_FAILED, TRACKED_DRIFT, UNTRACKED_CODE_QUERY_FAILED, UNTRACKED_CODE |
| Head/deploy | LOCAL_HEAD_QUERY_FAILED, START_HEAD_NOT_ANCESTOR, FETCH_FAILED, PUBLISHED_HEAD_QUERY_FAILED, BRANCH_DRIFT, LOCAL_HEAD_NOT_ANCESTOR_FINAL, DETACHED_CHECKOUT_FAILED, HEAD_VERIFY_QUERY_FAILED, HEAD_MISMATCH |
| Python boundary | PYTHON_NOT_AVAILABLE, PYTHON_START_FAILED, PYTHON_RESULT_INVALID |
| Source contract | RAW_EXPORT_INVALID_UTF8, RAW_EXPORT_INVALID_JSON, RAW_EXPORT_DUPLICATE_JSON_KEY, RAW_EXPORT_RESOURCE_LIMIT, RAW_EXPORT_REQUIRED_FILES, RAW_EXPORT_CAPTURE_CONTRACT_INVALID, RAW_EXPORT_EVIDENCE_HEAD, RAW_EXPORT_COMPARE_MISMATCH, RAW_EXPORT_CLOCK, RAW_EXPORT_REQUEST_WINDOW, RAW_EXPORT_SCHEDULE, RAW_EXPORT_SUMMARY_CONTRACT_OR_HASH |
| Files/publication | RAW_EXPORT_SYMLINK, RAW_EXPORT_OUTPUT_EXISTS, RAW_EXPORT_MISSING_OR_SYMLINK, RAW_EXPORT_SOURCE_CHANGED, RAW_EXPORT_LOCK_UNAVAILABLE, RAW_EXPORT_PERMISSION_DENIED, RAW_EXPORT_OUTPUT_RACE, RAW_EXPORT_PUBLICATION_FAILED, RAW_EXPORT_FILESYSTEM_FAILED |
| Code/unexpected | RAW_EXPORT_CODE_GATE_BLOCKED, RAW_EXPORT_CODE_CHANGED, RAW_EXPORT_UNEXPECTED_FAILURE, RUNNER_UNEXPECTED_FAILURE |

Only allowlisted codes can reach SUMMARY. Exception/stderr/Git/provider/payload text is never printed. Python stdout is captured: success requires exit0+SUCCESS; failure requires one valid JSON result and an allowlisted code; otherwise PYTHON_RESULT_INVALID. Unknown exceptions map to fixed unexpected codes.

## Preservation and boundaries

A/B/C/AB/BC/SUMMARY remain read-only. Existing output/partial paths block; no overwrite. Source bytes are rechecked before exclusive hard-link publication. Only a temporary file created by this invocation may be cleaned on failure. No merge/reset/clean, login, IG/broker call, order/cancel/modify or Candidate processing. NONE/false unchanged.

Tests cover fixed Python codes, invalid UTF8/JSON/source shape, permission/existence/filesystem/publication failures, source-byte preservation and absence of output/partial after failed publication. Static PowerShell tests enforce distinct gate codes and non-destructive/offline behavior. CI executes invalid-head and missing-root probes and requires exit2 plus exact HEAD_INVALID/HOST_UNAVAILABLE output.

Step2237 remains WAITING_EXTERNAL. The failed attempt is negative operational evidence only. The next single immutable-head runner output will either create the ZIP or name the next safe action—without a manual diagnostic chain.
