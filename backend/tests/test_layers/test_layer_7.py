"""Tests for Layer 7: Execution Engine."""
import pytest
import asyncio
import importlib.util
import sys
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path


def _load_execution_module():
    backend_root = Path(__file__).resolve().parents[2]
    # ensure backend is importable as a package
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    path = backend_root / "agent_framework" / "core" / "layers" / "07_execution.py"
    spec = importlib.util.spec_from_file_location("layer07", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def exec_mod():
    return _load_execution_module()


@pytest.fixture
def execution_engine(exec_mod):
    """Create ExecutionEngine with test timeout."""
    return exec_mod.ExecutionEngine(timeout_ms=1000, max_retries=3)


@pytest.fixture
def mock_tool():
    """Create mock tool object compatible with the ExecutionEngine expectations."""
    tool = MagicMock()
    tool.validate_params.return_value = None  # No validation error
    tool.estimated_cost.return_value = 0.01
    return tool


class TestExecutionSuccess:
    """Tests for successful execution."""

    @pytest.mark.asyncio
    async def test_execute_async_tool_success(self, execution_engine, mock_tool, exec_mod):
        """Test successful async tool execution."""
        mock_tool.run = AsyncMock(return_value={"data": "success"})

        result = await execution_engine.execute(
            mock_tool,
            {"param": "value"},
            request_id="test-123",
        )

        assert result.status == exec_mod.ExecutionStatus.SUCCESS
        assert result.output == {"data": "success"}
        assert result.error is None
        assert result.metrics.cost == 0.01
        mock_tool.run.assert_called_once_with(param="value")

    @pytest.mark.asyncio
    async def test_execute_sync_tool_success(self, execution_engine, mock_tool, exec_mod):
        """Test successful sync tool execution."""

        def sync_run(**kwargs):
            return {"data": "sync_success"}

        mock_tool.run = sync_run

        result = await execution_engine.execute(mock_tool, {})
        assert result.status == exec_mod.ExecutionStatus.SUCCESS
        assert result.output == {"data": "sync_success"}


class TestExecutionTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_execution_timeout(self, execution_engine, mock_tool, exec_mod):
        """Test timeout enforcement."""

        async def slow_run(**kwargs):
            await asyncio.sleep(10)  # Longer than 1s timeout
            return "should not reach"

        mock_tool.run = slow_run

        result = await execution_engine.execute(mock_tool, {})
        assert result.status == exec_mod.ExecutionStatus.TIMEOUT
        assert "exceeded" in (result.error or "")
        assert result.metrics.latency_ms >= 1000


class TestExecutionValidation:
    """Tests for parameter validation."""

    @pytest.mark.asyncio
    async def test_invalid_parameters(self, execution_engine, mock_tool, exec_mod):
        """Test invalid parameter handling."""
        mock_tool.validate_params.return_value = "Missing required param: X"

        result = await execution_engine.execute(mock_tool, {})
        assert result.status == exec_mod.ExecutionStatus.ERROR
        assert "Invalid parameters" in (result.error or "")
        # ensure run not called
        assert not getattr(mock_tool, "run", None) or mock_tool.run.call_count == 0


class TestExecutionError:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_tool_raises_exception(self, execution_engine, mock_tool, exec_mod):
        """Test exception handling."""
        mock_tool.run = AsyncMock(side_effect=ValueError("Tool error"))

        result = await execution_engine.execute(mock_tool, {})
        assert result.status == exec_mod.ExecutionStatus.ERROR
        assert "Tool execution failed" in (result.error or "")
        assert "Tool error" in (result.error or "")


class TestExecutionRetry:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, execution_engine, mock_tool, exec_mod):
        """Test retry succeeds after transient failure."""
        call_count = {"n": 0}

        async def flaky_run(**kwargs):
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise asyncio.TimeoutError("Temporary failure")
            return {"data": "success"}

        mock_tool.run = flaky_run

        result = await execution_engine.execute_with_retries(
            mock_tool,
            {},
            request_id="test-123",
        )
        assert result.status == exec_mod.ExecutionStatus.SUCCESS
        assert result.output == {"data": "success"}

    @pytest.mark.asyncio
    async def test_retry_exhausts_and_returns_error(self, execution_engine, mock_tool, exec_mod):
        """Test retry exhaustion returns final error."""
        async def always_fail(**kwargs):
            raise asyncio.TimeoutError("Always fail")

        mock_tool.run = always_fail
        result = await execution_engine.execute_with_retries(mock_tool, {})
        assert result.status in (exec_mod.ExecutionStatus.TIMEOUT, exec_mod.ExecutionStatus.ERROR)


class TestExecutionMetrics:
    """Tests for metric collection."""

    @pytest.mark.asyncio
    async def test_metrics_collected(self, execution_engine, mock_tool, exec_mod):
        """Test execution metrics are collected."""
        mock_tool.run = AsyncMock(return_value={"data": "test"})

        result = await execution_engine.execute(mock_tool, {})
        assert result.metrics is not None
        assert result.metrics.latency_ms >= 0
        assert result.metrics.cost == 0.01
        assert result.metrics.tokens_used == 0
