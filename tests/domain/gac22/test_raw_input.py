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
ZULU_MESSAGE = "Timestamps must be in UTC with the 'Z' notation."


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


def test_pt24h_passes() -> None:
    """The hour form of a day is accepted."""
    assert validate_raw_event(_event_with(("intervalPeriod", "duration"), "PT24H")) == []


@pytest.mark.parametrize("ts", ["2026-01-13T23:00:00+00:00", "2026-01-14T00:00:00+01:00"])
def test_non_zulu_timestamp_fails(ts: str) -> None:
    """An offset notation is rejected even when it denotes UTC."""
    start = validate_raw_event(_event_with(("intervalPeriod", "start"), ts))
    created = validate_raw_event({"createdDateTime": ts})

    assert [error["loc"] for error in start] == [("intervalPeriod", "start")]
    assert [error["loc"] for error in created] == [("createdDateTime",)]
    assert ZULU_MESSAGE in str(created[0]["type"])


def test_zulu_passes() -> None:
    """Uppercase and lowercase Zulu are both accepted."""
    data = {"createdDateTime": "2026-01-14T00:00:00Z", "modificationDateTime": "2026-01-14T00:00:00z"}

    assert validate_raw_event(data) == []


def test_event_name_p1d_not_flagged() -> None:
    """Only the listed fields are read, so free text is never flagged."""
    assert validate_raw_event({"eventName": "P1D"}) == []


def test_absent_and_null_fields_pass() -> None:
    """Missing, null and non-string values are left to the model parser."""
    data = {"intervalPeriod": None, "duration": None, "createdDateTime": None}

    assert validate_raw_event(data) == []
    assert validate_raw_event({"intervals": None}) == []
    assert validate_raw_event({"intervals": ["x", {"intervalPeriod": None}]}) == []
    assert validate_raw_event({"duration": 5, "createdDateTime": 7}) == []


def test_program_and_ven_timestamps_checked() -> None:
    """Programs and VENs get the same checks on their own fields."""
    ts = "2026-01-14T00:00:00+01:00"

    program = validate_raw_program({"createdDateTime": ts, "intervalPeriod": {"duration": "P1D"}})
    ven = validate_raw_ven({"modificationDateTime": ts})

    assert [error["loc"] for error in program] == [("createdDateTime",), ("intervalPeriod", "duration")]
    assert [error["loc"] for error in ven] == [("modificationDateTime",)]
