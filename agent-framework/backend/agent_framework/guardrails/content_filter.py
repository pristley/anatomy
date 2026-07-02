"""Content filter for PII, profanity and spam detection."""
from __future__ import annotations

import re
from typing import Dict, Any, List, Tuple

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\b(?:\+\d{1,3}[- ]?)?(?:\(\d{2,4}\)|\d{2,4})[- ]?\d{3,4}[- ]?\d{3,4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

PROFANITY = {"damn", "shit", "fuck", "bitch"}
SPAM_PHRASES = {"buy now", "click here", "free money", "work from home"}


def _find_profanity(text: str) -> List[Dict[str, Any]]:
    violations = []
    words = re.findall(r"\w+", text.lower())
    for w in words:
        if w in PROFANITY:
            violations.append({"type": "profanity", "text": w, "replacement": "***"})
    return violations


def _find_spam(text: str) -> List[Dict[str, Any]]:
    violations = []
    tl = text.lower()
    for phrase in SPAM_PHRASES:
        if phrase in tl:
            violations.append({"type": "spam", "text": phrase, "replacement": ""})
    # repeated char sequences
    if re.search(r"(.)\1{6,}", text):
        violations.append({"type": "spam", "text": "repeated_chars", "replacement": ""})
    return violations


def filter_content(text: str) -> Tuple[bool, List[Dict[str, Any]]]:
    violations: List[Dict[str, Any]] = []
    if EMAIL_RE.search(text):
        for m in EMAIL_RE.findall(text):
            violations.append({"type": "pii_email", "text": m, "replacement": "[REDACTED_EMAIL]"})

    if PHONE_RE.search(text):
        for m in PHONE_RE.findall(text):
            # PHONE_RE may capture groups; ensure string
            violations.append({"type": "pii_phone", "text": m, "replacement": "[REDACTED_PHONE]"})

    if SSN_RE.search(text):
        for m in SSN_RE.findall(text):
            violations.append({"type": "pii_ssn", "text": m, "replacement": "[REDACTED_SSN]"})

    if CC_RE.search(text):
        for m in CC_RE.findall(text):
            violations.append({"type": "pii_credit_card", "text": m, "replacement": "[REDACTED_CC]"})

    violations.extend(_find_profanity(text))
    violations.extend(_find_spam(text))

    safe = len(violations) == 0
    return safe, violations


__all__ = ["filter_content"]
# (previously a stray re-definition was here and removed)
