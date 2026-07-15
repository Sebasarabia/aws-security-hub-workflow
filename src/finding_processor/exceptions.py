# SPDX-License-Identifier: MIT-0
"""Domain exceptions with deliberately safe messages."""


class FindingProcessorError(Exception):
    """Base domain exception."""


class FindingValidationError(FindingProcessorError):
    """An event or finding did not meet the supported contract."""


class ConfigurationError(FindingProcessorError):
    """Runtime configuration is invalid."""


class NotificationError(FindingProcessorError):
    """A sanitized notification could not be published."""
