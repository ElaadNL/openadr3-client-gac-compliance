# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""
Raw-input checks for GAC 2.2 section 9.1.5.

Plugin validators run on the parsed pydantic model, where "P1D" and "PT24H" are the same timedelta and
"Z" and "+00:00" the same datetime. The two rules below can therefore only be checked on the raw JSON,
before it is parsed. Callers run these functions on the raw dict before parsing, and raise the result with
ValidationError.from_exception_data or report it. They are deliberately not registered in the plugin.

Field names are camelCase, as the VTN returns them. Absent, null and non-string values are skipped: the
model parser reports those.
"""

from collections.abc import Mapping
from typing import Any, Final, LiteralString

from pydantic_core import InitErrorDetails, PydanticCustomError

DAYS_ERROR_MESSAGE: Final = "Durations must not use days, such as 'P1D'. Use hours instead, such as 'PT24H'."
ZULU_ERROR_MESSAGE: Final = "Timestamps must be in UTC with the 'Z' notation."

_AUDIT_TIMESTAMP_FIELDS = ("createdDateTime", "modificationDateTime")


def _error(message: LiteralString, loc: tuple[str | int, ...], value: str) -> InitErrorDetails:
    return InitErrorDetails(type=PydanticCustomError("value_error", message), loc=loc, input=value, ctx={})


def _duration_errors(value: object, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
    if not isinstance(value, str):
        return []

    # The day designator belongs to the date part of an ISO 8601 duration, before the 'T'.
    date_part = value.split("T", 1)[0]
    uses_days = "D" in date_part
    if uses_days:
        return [_error(DAYS_ERROR_MESSAGE, loc, value)]
    return []


def _timestamp_errors(value: object, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
    if not isinstance(value, str):
        return []

    # RFC 3339 allows a lowercase 'z'.
    is_zulu = value.endswith(("Z", "z"))
    if not is_zulu:
        return [_error(ZULU_ERROR_MESSAGE, loc, value)]
    return []


def _audit_timestamp_errors(data: Mapping[str, Any]) -> list[InitErrorDetails]:
    errors: list[InitErrorDetails] = []
    for field in _AUDIT_TIMESTAMP_FIELDS:
        errors.extend(_timestamp_errors(data.get(field), (field,)))
    return errors


def _interval_period_errors(period: object, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
    if not isinstance(period, Mapping):
        return []
    return [
        *_timestamp_errors(period.get("start"), (*loc, "start")),
        *_duration_errors(period.get("duration"), (*loc, "duration")),
        *_duration_errors(period.get("randomizeStart"), (*loc, "randomizeStart")),
    ]


def validate_raw_event(data: Mapping[str, Any]) -> list[InitErrorDetails]:
    """Check the raw event JSON for day durations and non-Zulu timestamps."""
    errors = _audit_timestamp_errors(data)
    errors.extend(_interval_period_errors(data.get("intervalPeriod"), ("intervalPeriod",)))
    errors.extend(_duration_errors(data.get("duration"), ("duration",)))
    intervals = data.get("intervals")
    if isinstance(intervals, list):
        for index, interval in enumerate(intervals):
            if isinstance(interval, Mapping):
                errors.extend(
                    _interval_period_errors(interval.get("intervalPeriod"), ("intervals", index, "intervalPeriod"))
                )
    return errors


def validate_raw_program(data: Mapping[str, Any]) -> list[InitErrorDetails]:
    """Check the raw program JSON for day durations and non-Zulu timestamps."""
    errors = _audit_timestamp_errors(data)
    errors.extend(_interval_period_errors(data.get("intervalPeriod"), ("intervalPeriod",)))
    return errors


def validate_raw_ven(data: Mapping[str, Any]) -> list[InitErrorDetails]:
    """Check the raw VEN JSON for non-Zulu timestamps."""
    return _audit_timestamp_errors(data)
