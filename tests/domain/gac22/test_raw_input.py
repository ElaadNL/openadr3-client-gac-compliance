# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest

from openadr3_client_gac_compliance.gac22.raw_input import (
    validate_raw_event,
    validate_raw_program,
    validate_raw_ven,
)

DAYS_MESSAGE = "Durations must not use days, such as 'P1D'. Use hours instead, such as 'PT24H'."
FORMAT_MESSAGE = "Durations must be ISO 8601 strings, such as 'PT1H'."
ZULU_MESSAGE = "Timestamps must be RFC 3339 strings in UTC with the 'Z' notation"


def _event_with(path: tuple[str | int, ...], value: Any) -> dict[str, Any]:  # noqa: ANN401
    data: dict[str, Any] = {
        "intervalPeriod": {"start": "2026-01-14T00:00:00Z", "duration": "PT24H"},
        "intervals": [{"id": 0, "intervalPeriod": {"start": "2026-01-14T00:00:00Z", "duration": "PT1H"}}],
    }
    node: Any = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return data


@pytest.mark.parametrize(
    "path",
    [
        ("intervals", 0, "intervalPeriod", "duration"),
        ("intervalPeriod", "duration"),
        ("intervals", 0, "intervalPeriod", "randomizeStart"),
        ("duration",),
    ],
)
def test_p1d_fails(path: tuple[str | int, ...]) -> None:
    """A day duration is rejected at every place a duration is read."""
    errors = validate_raw_event(_event_with(path, "P1D"))

    assert [error["loc"] for error in errors] == [path]
    assert DAYS_MESSAGE in str(errors[0]["type"])


@pytest.mark.parametrize("duration", ["PT24H", "PT1H30M", "PT15M", "PT0.5S", "-PT1H", "P1W", "P1Y"])
def test_iso8601_duration_without_days_passes(duration: str) -> None:
    """ISO 8601 durations without the day designator pass; weeks and years are not named by the rule."""
    assert validate_raw_event(_event_with(("intervalPeriod", "duration"), duration)) == []


@pytest.mark.parametrize(
    "duration",
    [86400, 86400.0, "86400", "1 day", "P", "PT", "PT1D", "p1d", "P1\N{ARABIC-INDIC DIGIT ONE}D"],
    ids=["int", "float", "digit-string", "free-text", "bare-p", "bare-pt", "day-in-time", "lowercase", "arabic-indic"],
)
def test_non_iso8601_duration_fails(duration: object) -> None:
    """Shapes the parser accepts or OpenADR does not define, such as a number of seconds, are rejected."""
    errors = validate_raw_event(_event_with(("intervalPeriod", "duration"), duration))

    assert [error["loc"] for error in errors] == [("intervalPeriod", "duration")]
    assert FORMAT_MESSAGE in str(errors[0]["type"])


@pytest.mark.parametrize("ts", ["2026-01-13T23:00:00+00:00", "2026-01-14T00:00:00+01:00"])
def test_non_zulu_timestamp_fails(ts: str) -> None:
    """An offset notation is rejected even when it denotes UTC."""
    start = validate_raw_event(_event_with(("intervalPeriod", "start"), ts))
    created = validate_raw_event({"createdDateTime": ts})

    assert [error["loc"] for error in start] == [("intervalPeriod", "start")]
    assert [error["loc"] for error in created] == [("createdDateTime",)]
    assert ZULU_MESSAGE in str(created[0]["type"])


@pytest.mark.parametrize(
    "ts",
    [1768345200, 1768345200.0, "1768345200", "2026-01-13T23:00Z", "2026-01-13 23:00:00Z", "20260113T230000Z"],
    ids=["epoch-int", "epoch-float", "epoch-string", "no-seconds", "space-separator", "basic-format"],
)
def test_non_rfc3339_timestamp_fails(ts: object) -> None:
    """Shapes the parser accepts but RFC 3339 does not, such as Unix epoch numbers, are rejected."""
    errors = validate_raw_event({"createdDateTime": ts})

    assert [error["loc"] for error in errors] == [("createdDateTime",)]
    assert ZULU_MESSAGE in str(errors[0]["type"])


@pytest.mark.parametrize(
    "ts", ["2026-01-14T00:00:00Z", "2026-01-14T00:00:00z", "2026-01-14t00:00:00Z", "2026-01-14T00:00:00.000Z"]
)
def test_rfc3339_zulu_passes(ts: str) -> None:
    """RFC 3339 UTC timestamps pass, with lowercase 't' or 'z' and with or without milliseconds."""
    assert validate_raw_event({"createdDateTime": ts, "modificationDateTime": ts}) == []


def test_event_name_p1d_not_flagged() -> None:
    """Only the listed fields are read, so free text is never flagged."""
    assert validate_raw_event({"eventName": "P1D"}) == []


def test_absent_and_null_fields_pass() -> None:
    """Missing and null values are skipped; the fields are optional."""
    data = {"intervalPeriod": None, "duration": None, "createdDateTime": None}

    assert validate_raw_event(data) == []
    assert validate_raw_event({"intervals": None}) == []
    assert validate_raw_event({"intervals": ["x", {"intervalPeriod": None}]}) == []


def test_program_and_ven_timestamps_checked() -> None:
    """Programs and VENs get the same checks on their own fields."""
    ts = "2026-01-14T00:00:00+01:00"

    program = validate_raw_program({"createdDateTime": ts, "intervalPeriod": {"duration": "P1D"}})
    ven = validate_raw_ven({"modificationDateTime": ts})

    assert [error["loc"] for error in program] == [("createdDateTime",), ("intervalPeriod", "duration")]
    assert [error["loc"] for error in ven] == [("modificationDateTime",)]
