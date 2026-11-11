# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""
Raw-input checks for GAC 2.2 section 9.1.5.

Plugin validators run on the parsed pydantic model, where "P1D" and "PT24H" are the same timedelta and
"Z" and "+00:00" the same datetime. The two rules below can therefore only be checked on the raw JSON,
before it is parsed. Callers run these functions on the raw dict before parsing, and raise the result with
ValidationError.from_exception_data or report it. They are deliberately not registered in the plugin.

Field names are camelCase, as the VTN returns them. Absent and null values are skipped. Otherwise a
timestamp must be an RFC 3339 string and a duration an ISO 8601 string, as OpenADR 3.1 defines both: the
parser also accepts plain numbers (Unix epoch seconds, a number of seconds) and other shapes, so those are
rejected here.
"""

import re
from collections.abc import Mapping
from typing import Any, Final, LiteralString

from pydantic_core import InitErrorDetails, PydanticCustomError

DURATION_FORMAT_ERROR_MESSAGE: Final = "Durations must be ISO 8601 strings, such as 'PT1H'."
DAYS_ERROR_MESSAGE: Final = "Durations must not use days, such as 'P1D'. Use hours instead, such as 'PT24H'."
ZULU_ERROR_MESSAGE: Final = (
    "Timestamps must be RFC 3339 strings in UTC with the 'Z' notation, such as '2026-01-14T00:00:00.000Z'."
)

# RFC 3339 section 5.6 date-time with the UTC designator. The 'T' and 'Z' may be lowercase (section 5.6,
# NOTE); seconds are required, and the fraction of a second is optional.
_RFC3339_UTC: Final = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?[Zz]")

# The `duration` pattern of the OpenADR 3.1 OpenAPI file, with `\d` narrowed to ASCII digits.
_ISO8601_DURATION: Final = re.compile(
    r"(-?)P(?=[0-9]|T[0-9])(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)([DW]))?"
    r"(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?"
)

_AUDIT_TIMESTAMP_FIELDS = ("createdDateTime", "modificationDateTime")


def _error(message: LiteralString, loc: tuple[str | int, ...], value: object) -> InitErrorDetails:
    return InitErrorDetails(type=PydanticCustomError("value_error", message), loc=loc, input=value, ctx={})


def _duration_errors(value: object, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
    if value is None:
        return []

    if not isinstance(value, str) or _ISO8601_DURATION.fullmatch(value) is None:
        return [_error(DURATION_FORMAT_ERROR_MESSAGE, loc, value)]

    # The day designator belongs to the date part of an ISO 8601 duration, before the 'T'.
    date_part = value.split("T", 1)[0]
    uses_days = "D" in date_part
    if uses_days:
        return [_error(DAYS_ERROR_MESSAGE, loc, value)]
    return []


def _timestamp_errors(value: object, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
    if value is None:
        return []

    if not isinstance(value, str) or _RFC3339_UTC.fullmatch(value) is None:
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
