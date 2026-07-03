import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def get_request_id() -> str:
    try:
        return request_id_var.get()
    except LookupError:
        return ""
