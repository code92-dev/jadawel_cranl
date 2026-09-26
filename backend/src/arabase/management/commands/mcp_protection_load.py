"""Run the release-blocking MCP protection capacity and latency canary.

The command deliberately exercises the digest-only vault against a real Redis
server from multiple worker processes.  It never prints a Redis URL, token
handle, protected value, or exception text.  The command is opt-in because it
creates up to 50,000 short-lived test reservations in the configured vault.
"""

from __future__ import annotations

import base64
import json
import multiprocessing
import os
import secrets
import time
from dataclasses import asdict
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from redis import Redis
from redis.exceptions import RedisError

from arabase.mcp.protection.limits import ISSUER_LEASE_SECONDS
from arabase.mcp.protection.vault import (
    MASK_TOKEN_REDIS_PREFIX,
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    RedisMaskTokenVault,
)
from arabase.mcp.protection.vault.redis_backend import issuance_lease

TOKEN_MEMORY_ESTIMATE_BYTES = 50_000 * 1_536
MEMORY_ESTIMATE_TOLERANCE = 1.5
CONCURRENCY_HOLD_SECONDS = 0.4
CONCURRENCY_REJECTION_BUDGET_MS = 250


def _connect(redis_url: str) -> Redis:
    return Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=0.25,
        # The canary intentionally runs a large concurrent reservation batch.
        # Hosted CI runners can briefly pause Redis while its configured
        # no-eviction instance performs a background snapshot; keep the
        # timeout bounded, but avoid treating that short persistence pause as
        # a capacity failure.
        socket_timeout=2.0,
    )


def _issue_batch(payload: tuple[str, int, int, int]) -> dict:
    redis_url, endpoint_id, batch_index, token_count = payload
    redis = _connect(redis_url)
    vault = RedisMaskTokenVault(redis_client=redis)
    issued = 0
    first_token = None
    started = perf_counter()
    try:
        requests = []
        with issuance_lease(endpoint_id, vault):
            for token_index in range(token_count):
                binding = MaskTokenBinding(
                    endpoint_id=endpoint_id,
                    workspace_id=1,
                    table_id=1,
                    row_id=(batch_index * token_count) + token_index + 1,
                    field_id=1,
                    policy_revision=1,
                    access_generation=1,
                    operation_class="preserve_cell",
                    observed_row_state="load-test-state",
                    field_type="text",
                )
                requests.append(
                    (
                        binding,
                        f"load-test-value-{batch_index}-{token_index}",
                    )
                )
            tokens = vault.issue_many(requests)
        issued = len(tokens)
        if tokens:
            binding, value = requests[0]
            first_token = {
                "raw_handle": tokens[0].raw_handle,
                "binding": asdict(binding),
                "value": value,
            }
        return {
            "ok": True,
            "issued": issued,
            "duration_ms": (perf_counter() - started) * 1_000,
            "sample": first_token,
        }
    except (MaskTokenVaultUnavailable, RedisError) as exc:
        return {
            "ok": False,
            "issued": issued,
            "duration_ms": (perf_counter() - started) * 1_000,
            "error_type": type(exc).__name__,
            "sample": first_token,
        }
    finally:
        redis.close()


def _redeem_sample(payload: tuple[str, dict]) -> bool:
    redis_url, sample = payload
    redis = _connect(redis_url)
    try:
        vault = RedisMaskTokenVault(redis_client=redis)
        return vault.redeem(
            sample["raw_handle"],
            MaskTokenBinding(**sample["binding"]),
            sample["value"],
        )
    finally:
        redis.close()


def _issuer_spike(payload: tuple[str, int, float]) -> dict:
    redis_url, endpoint_id, start_at = payload
    redis = _connect(redis_url)
    vault = RedisMaskTokenVault(redis_client=redis)
    wait_seconds = max(0.0, start_at - time.time())
    if wait_seconds:
        time.sleep(wait_seconds)
    started = perf_counter()
    admitted = False
    try:
        with issuance_lease(endpoint_id, vault):
            admitted = True
            time.sleep(CONCURRENCY_HOLD_SECONDS)
    except (MaskTokenVaultUnavailable, RedisError):
        pass
    finally:
        redis.close()
    return {
        "admitted": admitted,
        "duration_ms": (perf_counter() - started) * 1_000,
    }


def _dead_issuer_worker(payload: tuple[str, int]) -> None:
    """Acquire a short lease and exit without cleanup like a killed worker."""

    redis_url, endpoint_id = payload
    redis = _connect(redis_url)
    try:
        vault = RedisMaskTokenVault(redis_client=redis)
        lease = issuance_lease(endpoint_id, vault)
        lease.__enter__()
        # Deliberately bypass the context manager's cleanup. Redis expiry is the
        # recovery mechanism used when a worker dies after admission.
        os._exit(0)
    except (MaskTokenVaultUnavailable, RedisError):
        os._exit(2)


def _delete_test_keys(redis: Redis) -> None:
    keys = list(redis.scan_iter(match=f"{MASK_TOKEN_REDIS_PREFIX}*"))
    if keys:
        redis.delete(*keys)


def _redis_limits(redis: Redis) -> tuple[int, int]:
    maxmemory = int(redis.config_get("maxmemory").get("maxmemory", 0))
    policy = redis.config_get("maxmemory-policy").get("maxmemory-policy")
    if maxmemory <= 0 or policy != "noeviction":
        raise CommandError("The selected Redis is not a bounded noeviction vault.")
    used_memory = int(redis.info("memory").get("used_memory", 0))
    return maxmemory, used_memory


class Command(BaseCommand):
    help = "Run the opt-in real-Redis MCP protection capacity canary."

    def add_arguments(self, parser):
        parser.add_argument(
            "--redis-url",
            default="",
            help="Dedicated Redis URL; defaults to MCP_PROTECTION_REDIS_URL.",
        )
        parser.add_argument("--calls", type=int, default=51)
        parser.add_argument("--tokens-per-call", type=int, default=1_000)
        parser.add_argument("--processes", type=int, default=3)
        parser.add_argument("--endpoints", type=int, default=5)
        parser.add_argument("--skip-concurrency", action="store_true")
        parser.add_argument("--skip-recovery", action="store_true")
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Acknowledge that the command creates and deletes test vault keys.",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("Pass --yes to run the destructive load canary.")
        if options["calls"] < 51 or options["tokens_per_call"] < 1:
            raise CommandError("The canary requires at least 51 calls.")
        if options["processes"] < 3 or options["endpoints"] < 5:
            raise CommandError(
                "The canary requires at least 3 processes and 5 endpoints."
            )

        redis_url = options["redis_url"] or settings.MCP_PROTECTION_REDIS_URL
        if not redis_url:
            raise CommandError(
                "This canary exercises the optional Redis vault and needs its URL. "
                "The default PostgreSQL vault needs no Redis."
            )

        # The canary's values are synthetic and the key is process-local. This
        # avoids relying on a production fingerprint key while still exercising
        # the exact vault canonicalization and HMAC path.
        settings.MCP_PROTECTION_FINGERPRINT_KEYS = {
            "load-test": base64.b64encode(secrets.token_bytes(32)).decode()
        }
        settings.MCP_PROTECTION_ACTIVE_KEY_ID = "load-test"

        redis = _connect(redis_url)
        try:
            redis.ping()
            _delete_test_keys(redis)
            maxmemory, before_memory = _redis_limits(redis)

            context = multiprocessing.get_context("fork")
            batch_payloads = [
                (
                    redis_url,
                    100 + (index % options["endpoints"]),
                    index,
                    options["tokens_per_call"],
                )
                for index in range(options["calls"] - 1)
            ]
            with context.Pool(processes=options["processes"]) as pool:
                # The default Pool chunk size would hand the same first five
                # endpoint ids to every worker. With the real two-issuer
                # endpoint ceiling, that creates an artificial three-way
                # collision and makes the release gate timing-dependent.
                successful_batches = pool.map(_issue_batch, batch_payloads, chunksize=1)

            if not all(item["ok"] for item in successful_batches):
                failures = [item for item in successful_batches if not item["ok"]]
                # Keep the failure content-blind while making hosted-runner
                # diagnosis actionable.  Exception classes and issued counts
                # contain no handles, values, URLs, or request payloads.
                failure_summary = ",".join(
                    sorted(
                        f"{item.get('error_type', 'unknown')}:{item['issued']}"
                        for item in failures
                    )
                )
                raise CommandError(
                    "A token-load batch failed before the quota boundary "
                    f"({failure_summary})."
                )
            issued = sum(item["issued"] for item in successful_batches)
            expected_issued = (options["calls"] - 1) * options["tokens_per_call"]
            if issued != expected_issued:
                raise CommandError("The token-load canary issued an unexpected count.")

            rejected = _issue_batch(
                (
                    redis_url,
                    100,
                    options["calls"] - 1,
                    options["tokens_per_call"],
                )
            )
            if rejected["ok"] or rejected["issued"] != 0:
                raise CommandError("The quota-boundary call did not fail closed.")

            samples = [item["sample"] for item in successful_batches if item["sample"]]
            if not samples:
                raise CommandError("The token-load canary did not produce a sample.")
            with context.Pool(processes=1) as pool:
                cross_worker_redeemed = pool.map(
                    _redeem_sample, [(redis_url, samples[0])]
                )[0]
            if not cross_worker_redeemed:
                raise CommandError("Cross-worker token redemption failed.")

            _maxmemory, after_memory = _redis_limits(redis)
            memory_delta = max(0, after_memory - before_memory)
            memory_budget = TOKEN_MEMORY_ESTIMATE_BYTES * MEMORY_ESTIMATE_TOLERANCE
            if memory_delta > memory_budget:
                raise CommandError("Token vault memory exceeded the release budget.")

            concurrency_result = None
            if not options["skip_concurrency"]:
                start_at = time.time() + 0.5
                spike_payloads = [
                    (
                        redis_url,
                        200 + (index % options["endpoints"]),
                        start_at,
                    )
                    for index in range(12)
                ]
                with context.Pool(processes=12) as pool:
                    spike = pool.map(_issuer_spike, spike_payloads)
                admitted_count = sum(item["admitted"] for item in spike)
                rejected_durations = [
                    item["duration_ms"] for item in spike if not item["admitted"]
                ]
                if admitted_count != 6 or not rejected_durations:
                    raise CommandError("The six-issuer concurrency gate did not hold.")
                if max(rejected_durations) > CONCURRENCY_REJECTION_BUDGET_MS:
                    raise CommandError("Issuer rejection exceeded the 250ms budget.")
                concurrency_result = {
                    "admitted": admitted_count,
                    "rejected": len(rejected_durations),
                    "max_rejected_ms": round(max(rejected_durations), 2),
                }

            worker_recovery = None
            if not options["skip_recovery"]:
                dead_worker = context.Process(
                    target=_dead_issuer_worker,
                    args=((redis_url, 900),),
                )
                dead_worker.start()
                dead_worker.join(timeout=ISSUER_LEASE_SECONDS + 1)
                if dead_worker.is_alive() or dead_worker.exitcode != 0:
                    dead_worker.kill()
                    dead_worker.join()
                    raise CommandError("Worker-death recovery setup failed.")
                time.sleep(ISSUER_LEASE_SECONDS + 0.2)
                try:
                    with issuance_lease(900, RedisMaskTokenVault(redis_client=redis)):
                        pass
                except (MaskTokenVaultUnavailable, RedisError) as exc:
                    raise CommandError(
                        "Expired worker lease was not reclaimed."
                    ) from exc
                worker_recovery = {
                    "dead_worker_reclaimed": True,
                    "lease_seconds": ISSUER_LEASE_SECONDS,
                }

            durations = sorted(item["duration_ms"] for item in successful_batches)
            p95_index = min(len(durations) - 1, int(len(durations) * 0.95))
            self.stdout.write(
                json.dumps(
                    {
                        "calls_succeeded": len(successful_batches),
                        "quota_boundary_rejected": True,
                        "issued_tokens": issued,
                        "cross_worker_redemption": cross_worker_redeemed,
                        "redis_maxmemory_bytes": maxmemory,
                        "redis_memory_delta_bytes": memory_delta,
                        "redis_memory_delta_mib": round(memory_delta / 1_048_576, 2),
                        "batch_p95_ms": round(durations[p95_index], 2),
                        "concurrency": concurrency_result,
                        "worker_recovery": worker_recovery,
                    },
                    sort_keys=True,
                )
            )
        except (RedisError, OSError, ValueError, TypeError) as exc:
            raise CommandError(
                f"MCP protection load canary failed: {type(exc).__name__}"
            ) from exc
        finally:
            try:
                _delete_test_keys(redis)
            except (RedisError, OSError, ValueError, TypeError):
                # Redis may be the dependency that failed. Cleanup is best
                # effort and must never replace the fixed safe error with a
                # connection traceback or exception details.
                pass
            finally:
                redis.close()
