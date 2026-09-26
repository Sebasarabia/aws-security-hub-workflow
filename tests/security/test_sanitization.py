# SPDX-License-Identifier: MIT-0
"""Untrusted text and identifier sanitization."""

import pytest

from finding_processor.sanitization import (
    mask_account_id,
    sanitize_resource_identifier,
    sanitize_text,
    shorten_identifier,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hello\nERROR forged", "hello ERROR forged"),
        ("null\x00byte", "nullbyte"),
        ("carriage\rreturn", "carriage return"),
        ("Bolivia — acción 中文", "Bolivia — acción 中文"),
        (None, ""),
    ],
)
def test_sanitize_text(raw: object, expected: str) -> None:
    assert sanitize_text(raw, max_length=100) == expected


def test_length_account_and_identifier_helpers() -> None:
    assert sanitize_text("a" * 500, max_length=20) == "a" * 20
    assert mask_account_id("123456789012") == "********9012"
    assert mask_account_id("x") == "UNKNOWN"
    assert shorten_identifier("arn:aws:test:region:123456789012:thing/abcdef", visible=4) == "…cdef"
    assert sanitize_resource_identifier(None) is None
