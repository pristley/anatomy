"""Layer 8: Resilience & Error Recovery.

Provides a simple CircuitBreaker implementation and a coordinating
`ResilienceLayer` that classifies errors and applies resilience strategies.

Spec: RESIL-001
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal, accepting requests
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if recovered


class ErrorSeverity(str, Enum):
    """Error severity classification."""

    TRANSIENT = "transient"  # Retry (timeout, connection)
    RETRIABLE = "retriable"  # Try alternative (rate limit)
    TERMINAL = "terminal"  # No retry (invalid param)
    UNKNOWN = "unknown"  # Default


@dataclass
class ErrorContext:
    """Rich error information for debugging.

    Attributes:
        error_type: Python exception type name
        error_message: Human-readable error message
        severity: ErrorSeverity classification
        layer: Which layer the error occurred in
        timestamp: When the error occurred
        request_id: Request ID for tracing
        attempt_number: Which retry attempt this was
        additional_info: Custom error metadata
    """

    error_type: str
    error_message: str
    severity: ErrorSeverity
    layer: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    attempt_number: int = 0
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging."""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "layer": self.layer,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "attempt_number": self.attempt_number,
            "additional_info": self.additional_info,
        }


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""


class CircuitBreaker:
    """Circuit breaker for fault isolation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(
        self,
        threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "default",
    ):
        """Initialize CircuitBreaker.

        Args:
            threshold: Failure count to trigger open (default: 5)
            timeout: Seconds before attempting recovery (default: 60)
            expected_exception: Exception type to catch (default: all)
            name: Circuit breaker name for logging
        """
        self.threshold = int(threshold)
        self.timeout = float(timeout)
        self.expected_exception = expected_exception
        self.name = name

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (should reject requests)."""
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # Try recovery after timeout
            if self.last_failure_time:
                elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
                if elapsed > self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0  # Reset for testing
                    return False  # Allow test request
            return True  # Still failing, reject

        # HALF_OPEN state - let requests through to test recovery
        return False

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
            Original exception: If call fails
        """
        if self.is_open():
            raise CircuitBreakerOpen(
                f"Circuit breaker '{self.name}' is OPEN; failing fast. Retry after {self.timeout}s"
            )

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception:
            self.on_failure()
            raise

    def on_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # A small number of successful probes closes the circuit
            if self.success_count >= 2:
                self.state = CircuitState.CLOSED
                self.failure_count = 0

    def on_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN


class ResilienceLayer:
    """Central resilience strategy coordinator.

    Manages circuit breakers per service and chooses recovery strategies.
    """

    def __init__(self) -> None:
        """Initialize resilience layer."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def classify_error(self, error: Exception) -> ErrorSeverity:
        """Classify error to determine recovery strategy.

        Args:
            error: Exception to classify

        Returns:
            ErrorSeverity enum value
        """
        error_type = type(error).__name__

        # Transient errors (retry immediately)
        if error_type in ("TimeoutError", "asyncio.TimeoutError"):
            return ErrorSeverity.TRANSIENT
        if error_type in ("ConnectionError", "ConnectionResetError"):
            return ErrorSeverity.TRANSIENT

        # Retriable errors (try alternative or wait)
        if error_type in ("HTTPError", "429"):
            return ErrorSeverity.RETRIABLE

        # Terminal errors (don't retry)
        if error_type in ("ValueError", "TypeError", "KeyError"):
            return ErrorSeverity.TERMINAL

        return ErrorSeverity.UNKNOWN

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(name=service_name)
        return self.circuit_breakers[service_name]

    async def execute_with_resilience(
        self,
        func: Callable[..., Any],
        service_name: str,
        *args,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute function with full resilience strategy.

        Returns a dict with `success`, `output`, `error_context`, and
        `recovery_strategy` keys useful for higher-level orchestration.
        """
        cb = self.get_circuit_breaker(service_name)

        try:
            result = await cb.call(func, *args, **kwargs)
            return {
                "success": True,
                "output": result,
                "error_context": None,
                "recovery_strategy": "none",
            }

        except CircuitBreakerOpen as e:
            ctx = ErrorContext(
                error_type="CircuitBreakerOpen",
                error_message=str(e),
                severity=ErrorSeverity.RETRIABLE,
                layer="resilience",
                request_id=request_id,
            )
            return {
                "success": False,
                "output": None,
                "error_context": ctx,
                "recovery_strategy": "wait_and_retry",
            }

        except Exception as e:
            severity = self.classify_error(e)
            ctx = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                severity=severity,
                layer="execution",
                request_id=request_id,
            )

            if severity == ErrorSeverity.TRANSIENT:
                strategy = "retry_with_backoff"
            elif severity == ErrorSeverity.RETRIABLE:
                strategy = "try_alternative"
            else:
                strategy = "fail_fast"

            return {
                "success": False,
                "output": None,
                "error_context": ctx,
                "recovery_strategy": strategy,
            }


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpen",
    "ErrorContext",
    "ErrorSeverity",
    "ResilienceLayer",
]
