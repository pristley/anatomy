"""Layer 7: Execution Engine - Tool invocation with safety bounds.

Provides ExecutionEngine that runs tools with timeouts and retry/backoff.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Protocol
from enum import Enum
from agent_framework.core.types import ExecutionMetrics


class ToolProtocol(Protocol):
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]: ...

    def run(self, **params: Any) -> Any:  # sync
        ...

    async def run_async(self, **params: Any) -> Any:  # async alternative name
        ...

    def estimated_cost(self, **params: Any) -> float: ...


class ExecutionStatus(str, Enum):
    """Execution outcome status."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


class ExecutionResult:
    """Result of a tool execution.

    Attributes:
        status: ExecutionStatus enum value
        output: Tool output (if successful)
        error: Error message (if failed)
        metrics: ExecutionMetrics with timing/cost
    """

    def __init__(
        self,
        status: ExecutionStatus,
        output: Optional[Any] = None,
        error: Optional[str] = None,
        metrics: Optional[ExecutionMetrics] = None,
    ) -> None:
        self.status = status
        self.output = output
        self.error = error
        self.metrics = metrics or ExecutionMetrics()


class ExecutionEngine:
    """Execute tools with safety bounds (timeout, budget).

    Features:
    - Async/sync tool support
    - Timeout enforcement
    - Parameter validation
    - Retry with exponential backoff
    - Cost tracking
    """

    def __init__(
        self,
        timeout_ms: int = 30000,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        """Initialize ExecutionEngine.

        Args:
            timeout_ms: Execution timeout in milliseconds (default: 30s)
            max_retries: Maximum retry attempts (default: 3)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
        """
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def execute(
        self,
        tool: ToolProtocol,
        params: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a tool with timeout enforcement.

        Args:
            tool: Tool instance to execute
            params: Tool parameters
            request_id: Request ID for tracking

        Returns:
            ExecutionResult with status, output, error, metrics

        Raises:
            None (always returns ExecutionResult, never raises)
        """
        start_time = time.monotonic()

        try:
            # Validate tool parameters
            validation_error = None
            try:
                validation_error = tool.validate_params(params)
            except Exception:
                # If validation is not implemented, ignore
                validation_error = None
            if validation_error:
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    error=f"Invalid parameters: {validation_error}",
                    metrics=ExecutionMetrics(latency_ms=0),
                )

            # Execute with timeout
            timeout_sec = self.timeout_ms / 1000.0

            # Prefer explicit async run method if available
            run_coro = None
            if hasattr(tool, "run_async") and asyncio.iscoroutinefunction(
                getattr(tool, "run_async")
            ):
                run_coro = tool.run_async(**params)
            elif asyncio.iscoroutinefunction(getattr(tool, "run", None)):
                run_coro = tool.run(**params)

            if run_coro is not None:
                output = await asyncio.wait_for(run_coro, timeout=timeout_sec)
            else:
                # Wrap sync in async
                loop = asyncio.get_event_loop()
                output = await asyncio.wait_for(
                    loop.run_in_executor(None, tool.run, **params),
                    timeout=timeout_sec,
                )

            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            cost = 0.0
            try:
                cost = float(tool.estimated_cost(**params))
            except Exception:
                cost = 0.0
            metrics = ExecutionMetrics(
                latency_ms=elapsed_ms,
                cost=cost,
                tokens_used=0,  # Updated by observability layer
            )

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                output=output,
                metrics=metrics,
            )

        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"Tool execution exceeded {self.timeout_ms}ms timeout",
                metrics=ExecutionMetrics(latency_ms=elapsed_ms),
            )

        except asyncio.CancelledError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return ExecutionResult(
                status=ExecutionStatus.CANCELLED,
                error="Tool execution was cancelled",
                metrics=ExecutionMetrics(latency_ms=elapsed_ms),
            )

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"Tool execution failed: {str(e)}",
                metrics=ExecutionMetrics(latency_ms=elapsed_ms),
            )

    async def execute_with_retries(
        self,
        tool: ToolProtocol,
        params: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute tool with exponential backoff retry logic.

        Only retries on transient errors (timeout, connection issues).
        Terminal errors (invalid params) don't retry.

        Args:
            tool: Tool to execute
            params: Tool parameters
            request_id: Request ID for tracking

        Returns:
            ExecutionResult (either success or final failure)
        """
        result: Optional[ExecutionResult] = None
        for attempt in range(self.max_retries):
            result = await self.execute(tool, params, request_id)

            # Success = return immediately
            if result.status == ExecutionStatus.SUCCESS:
                return result

            # Timeout = retry with backoff
            if (
                result.status == ExecutionStatus.TIMEOUT
                and attempt < self.max_retries - 1
            ):
                wait_time = self.backoff_factor**attempt
                await asyncio.sleep(wait_time)
                continue

            # Terminal error or out of retries = return failure
            return result

        return result or ExecutionResult(
            status=ExecutionStatus.ERROR, error="No result produced"
        )


__all__ = ["ExecutionEngine", "ExecutionResult", "ExecutionStatus"]


__all__ = ["ExecutionEngine"]
