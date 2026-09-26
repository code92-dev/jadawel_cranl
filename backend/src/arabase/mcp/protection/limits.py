"""Every tunable number of MCP field protection, in one leaf module.

Readers import the module and read ``limits.NAME`` at call time, so a test that
patches a value here changes it for every reader. This module imports nothing.
"""

# Mask-token vault.
MASK_TOKEN_TTL_SECONDS = 24 * 60 * 60
MAX_ISSUANCE_MEMORY_RATIO = 0.60
MAX_ENDPOINT_TOKENS = 10_000
MAX_GLOBAL_TOKENS = 50_000
PURGE_BATCH_SIZE = 500

# Issuer admission.
MAX_ACTIVE_ISSUERS_PER_ENDPOINT = 2
MAX_ACTIVE_ISSUERS_GLOBAL = 6
ISSUER_LEASE_SECONDS = 2
# Keep a 50 ms scheduling/serialization margin under the externally promised
# 250 ms rejection ceiling.  The semaphore itself therefore waits no longer
# than 200 ms before failing closed.
ISSUER_WAIT_SECONDS = 0.20

# Per-call egress.
MAX_ROWS_PER_CALL = 200
MAX_ISSUED_OR_REDEEMED_PER_CALL = 1000
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

# Readiness.
READINESS_OPERATION_TIMEOUT_SECONDS = 0.5
# Redis memory use at or above this ratio is logged as an alert.
REDIS_MEMORY_ALERT_RATIO = 0.70
