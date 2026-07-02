from typing import Any, Dict, List, Tuple


class SchemaValidator:
    @staticmethod
    def validate_params(params: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Any]]:
        errors: List[str] = []
        sanitized: Dict[str, Any] = {}

        for key, rules in (schema or {}).items():
            required = rules.get("required", False)
            expected_type = rules.get("type", None)

            if required and key not in params:
                errors.append(f"missing_required:{key}")
                continue

            if key not in params:
                continue

            val = params[key]

            # type check
            if expected_type and not isinstance(val, expected_type):
                errors.append(f"type_mismatch:{key}")
                continue

            # simple unsafe string detection (basic SQL/injection heuristics)
            if isinstance(val, str):
                lowered = val.lower()
                suspicious_tokens = ["drop ", "delete ", ";", "--", "/*", "*/", "union ", "insert "]
                if any(tok in lowered for tok in suspicious_tokens):
                    errors.append(f"unsafe_input:{key}")
                    # do not include original unsafe string in sanitized output
                    sanitized[key] = ""
                    continue

            sanitized[key] = val

        valid = len(errors) == 0
        return valid, errors, sanitized


__all__ = ["SchemaValidator"]
