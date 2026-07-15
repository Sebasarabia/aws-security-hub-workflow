# SPDX-License-Identifier: MIT-0
"""Sanitization and safe identifier helpers."""

from __future__ import annotations

import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def sanitize_text(value: object, *, max_length: int) -> str:
    """Preserve international text while removing log-forging controls/newlines."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    text = _CONTROL.sub("", text.replace("\r", " ").replace("\n", " "))
    return _WHITESPACE.sub(" ", text).strip()[:max_length]


def mask_account_id(account_id: str | None) -> str:
    clean = re.sub(r"\D", "", account_id or "")
    return f"********{clean[-4:]}" if len(clean) >= 4 else "UNKNOWN"


def shorten_identifier(identifier: str | None, *, visible: int = 12) -> str:
    clean = sanitize_text(identifier, max_length=512)
    if not clean:
        return "UNKNOWN"
    tail = clean.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return tail if len(tail) <= visible else f"…{tail[-visible:]}"


def sanitize_resource_identifier(identifier: object) -> str | None:
    clean = sanitize_text(identifier, max_length=512)
    if not clean:
        return None
    # Retain only a short non-account-bearing suffix in the normalized object.
    return shorten_identifier(clean, visible=48)
