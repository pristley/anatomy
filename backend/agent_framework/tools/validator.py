"""Parameter schema validator and sanitizer."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


class SchemaValidator:
    SQL_BLACKLIST = [";", "--", "/*", "*/", "drop ", "delete ", "insert ", "update "]
    CMD_BLACKLIST = [";", "&&", "||", "`", "$(`", "$ ", "|"]

    @staticmethod
    def _is_safe_string(s: str) -> bool:
        low = s.lower()
        for p in SchemaValidator.SQL_BLACKLIST + SchemaValidator.CMD_BLACKLIST:
            if p in low:
                return False
        return True

    @staticmethod
    def validate_params(params: Dict[str, Any], schema: Dict[str, Any] | None) -> Tuple[bool, List[str], Dict[str, Any]]:
        errors: List[str] = []
        sanitized = dict(params or {})

        if not schema:
            return True, [], sanitized

        for key, spec in schema.items():
            if isinstance(spec, dict) and spec.get("required") and key not in params:
                errors.append(f"missing required {key}")
                continue

            if key in params:
                val = params[key]
                expected = spec.get("type") if isinstance(spec, dict) else spec
                if expected and not isinstance(val, expected):
                    # allow int where float expected
                    if expected == float and isinstance(val, int):
                        sanitized[key] = float(val)
                    else:
                        errors.append(f"{key} type mismatch expected {expected}")

                # string safety checks
                if isinstance(val, str) and not SchemaValidator._is_safe_string(val):
                    errors.append(f"unsafe value for {key}")
                    sanitized[key] = re.sub(r"[;`|&$]", "", val)

        valid = len(errors) == 0
        return valid, errors, sanitized


__all__ = ["SchemaValidator"]
