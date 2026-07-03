import contextvars

# Shared context variables for observability and tracing
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")
