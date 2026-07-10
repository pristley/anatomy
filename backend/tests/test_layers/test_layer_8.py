import asyncio
import importlib

import pytest

mod = importlib.import_module("agent_framework.core.layers.08_resilience")
CircuitBreaker = mod.CircuitBreaker
CircuitBreakerOpen = mod.CircuitBreakerOpen
ResilienceLayer = mod.ResilienceLayer
ErrorSeverity = mod.ErrorSeverity


async def _succeed():
    return "ok"


async def _fail_transient():
    raise TimeoutError("timed out")


async def _fail_value():
    raise ValueError("bad")


@pytest.mark.asyncio
class TestCircuitBreakerStates:
    async def test_initial_closed(self):
        cb = CircuitBreaker()
        assert not cb.is_open()
        assert cb.state.value == "closed"

    async def test_failure_increment(self):
        cb = CircuitBreaker(threshold=3)
        cb.on_failure()
        cb.on_failure()
        assert cb.failure_count == 2
        assert cb.state.value == "closed"

    async def test_threshold_opens(self):
        cb = CircuitBreaker(threshold=2)
        cb.on_failure()
        cb.on_failure()
        assert cb.state.value == "open"
        assert cb.is_open()

    async def test_timeout_moves_to_half_open(self):
        cb = CircuitBreaker(threshold=1, timeout=0.05)
        cb.on_failure()
        assert cb.state.value == "open"
        # wait longer than timeout
        await asyncio.sleep(0.06)
        # is_open should flip to allow a probe and set HALF_OPEN
        assert not cb.is_open()
        assert cb.state.value == "half_open"

    async def test_success_in_half_open_closes(self):
        cb = CircuitBreaker(threshold=1, timeout=0.01)
        cb.on_failure()
        await asyncio.sleep(0.02)
        # trigger is_open check to move to HALF_OPEN if timeout elapsed
        assert not cb.is_open()
        assert cb.state.value == "half_open"
        # two successful probes close
        cb.on_success()
        assert cb.state.value == "half_open"
        cb.on_success()
        assert cb.state.value == "closed"


@pytest.mark.asyncio
class TestCircuitBreakerFaultIsolation:
    async def test_open_raises_immediately(self):
        cb = CircuitBreaker(threshold=1)
        cb.on_failure()
        with pytest.raises(CircuitBreakerOpen):
            await cb.call(_succeed)

    async def test_half_open_allows_call(self):
        cb = CircuitBreaker(threshold=1, timeout=0.01)
        cb.on_failure()
        await asyncio.sleep(0.02)
        # half-open should allow the call
        res = await cb.call(_succeed)
        assert res == "ok"

    async def test_success_resets_failure_count(self):
        cb = CircuitBreaker(threshold=1, timeout=0.01)
        cb.on_failure()
        await asyncio.sleep(0.02)
        await cb.call(_succeed)
        # after successful probes, circuit should be closed
        # give a second probe
        await cb.call(_succeed)
        assert cb.state.value == "closed"
        assert cb.failure_count == 0


class TestErrorClassification:
    def test_timeout_is_transient(self):
        rl = ResilienceLayer()
        sev = rl.classify_error(TimeoutError())
        assert sev == ErrorSeverity.TRANSIENT

    def test_connection_is_transient(self):
        rl = ResilienceLayer()
        sev = rl.classify_error(ConnectionError())
        assert sev == ErrorSeverity.TRANSIENT

    def test_http_is_retriable(self):
        class HTTPError(Exception):
            pass

        rl = ResilienceLayer()
        sev = rl.classify_error(HTTPError())
        assert sev == ErrorSeverity.RETRIABLE

    def test_value_is_terminal(self):
        rl = ResilienceLayer()
        sev = rl.classify_error(ValueError())
        assert sev == ErrorSeverity.TERMINAL


@pytest.mark.asyncio
class TestResilienceStrategy:
    async def test_execute_success(self):
        rl = ResilienceLayer()
        out = await rl.execute_with_resilience(_succeed, "svc-success")
        assert out["success"] is True
        assert out["output"] == "ok"

    async def test_execute_breaker_open(self):
        rl = ResilienceLayer()
        cb = rl.get_circuit_breaker("svc-open")
        cb.threshold = 1
        cb.on_failure()  # opens
        res = await rl.execute_with_resilience(_succeed, "svc-open")
        assert res["success"] is False
        assert res["recovery_strategy"] == "wait_and_retry"
        assert res["error_context"].error_type == "CircuitBreakerOpen"

    async def test_execute_transient_error_strategy(self):
        rl = ResilienceLayer()
        res = await rl.execute_with_resilience(_fail_transient, "svc-transient")
        assert res["success"] is False
        assert res["recovery_strategy"] == "retry_with_backoff"
