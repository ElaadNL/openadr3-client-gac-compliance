# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac22.event_coverage import two_day_window
from tests.domain.gac22.factories import continuous_event, existing_event, separated_event

COVERAGE_ERROR = "two full local calendar days"
START = datetime.fromisoformat("2026-01-13T23:00Z")
HOUR = timedelta(hours=1)


def dt(value: str) -> datetime:
    """Parse an ISO 8601 timestamp with an offset."""
    return datetime.fromisoformat(value)


def test_window_normal_day() -> None:
    """Outside DST changes the window runs from 23:00 UTC to 23:00 UTC two days later."""
    assert two_day_window(date(2026, 1, 14)) == (dt("2026-01-13T23:00Z"), dt("2026-01-15T23:00Z"))


def test_window_dst_start_is_47h() -> None:
    """The window over 28 and 29 March loses the hour DST skips."""
    start, end = two_day_window(date(2026, 3, 28))
    assert end - start == timedelta(hours=47)


def test_window_dst_end_is_49h() -> None:
    """The window over 24 and 25 October gains the hour DST repeats."""
    start, end = two_day_window(date(2026, 10, 24))
    assert end - start == timedelta(hours=49)


def test_continuous_48h_passes() -> None:
    """48 hourly intervals from local midnight cover two ordinary days."""
    continuous_event(START, 48)


def test_continuous_47h_dst_start_passes() -> None:
    """47 hourly intervals cover the two days on which DST starts."""
    continuous_event(dt("2026-03-27T23:00Z"), 47)


def test_continuous_49h_dst_end_passes() -> None:
    """49 hourly intervals cover the two days on which DST ends."""
    continuous_event(dt("2026-10-23T22:00Z"), 49)


def test_48h_across_dst_start_fails() -> None:
    """48 hours over the DST start run one hour past local midnight."""
    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        continuous_event(dt("2026-03-27T23:00Z"), 48)


def test_start_at_utc_midnight_fails() -> None:
    """UTC midnight is 01:00 in Amsterdam, so the event does not start at local midnight."""
    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        continuous_event(dt("2026-01-14T00:00Z"), 48)


def test_separated_gap_fails() -> None:
    """A one-hour gap between separated intervals leaves part of the window uncovered."""
    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        separated_event([(START, 24 * HOUR), (START + 25 * HOUR, 23 * HOUR)])


def test_separated_overlap_without_gap_passes() -> None:
    """Overlapping separated intervals still cover the window together."""
    separated_event([(START, 25 * HOUR), (START + 24 * HOUR, 24 * HOUR)])


def test_separated_out_of_time_order_passes() -> None:
    """Coverage does not depend on the order the intervals are listed in."""
    separated_event([(START + 24 * HOUR, 24 * HOUR), (START, 24 * HOUR)])


def test_event_duration_shortening_fails() -> None:
    """An event duration shorter than the intervals cuts the event off after one day."""
    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        continuous_event(START, 48, duration=timedelta(hours=24))


def test_event_duration_matching_passes() -> None:
    """An event duration equal to the window leaves the coverage intact."""
    continuous_event(START, 48, duration=timedelta(hours=48))


def test_created_day_before_passes() -> None:
    """An event published on 13 January covers 14 and 15 January."""
    existing_event(START, 48, created=dt("2026-01-13T06:30Z"))


def test_created_same_day_fails() -> None:
    """An event published on 14 January must cover 15 and 16 January, not 14 and 15."""
    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        existing_event(START, 48, created=dt("2026-01-14T06:30Z"))


def test_created_late_utc_is_next_local_day() -> None:
    """23:30 UTC on 13 Jan is already 14 Jan in Amsterdam, so the event must cover 15 and 16 Jan."""
    created = dt("2026-01-13T23:30Z")

    with pytest.raises(ValidationError, match=COVERAGE_ERROR):
        existing_event(START, 48, created=created)
    existing_event(START + 24 * HOUR, 48, created=created)
