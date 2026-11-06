# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""
Validates the two-day coverage rule of GAC 2.2.0, section 10.3.2.

Each event must cover the two local calendar days after the day it is published, from local midnight at the
start of the first day to local midnight at the end of the second day. Because the days are local, the
window is 47 hours when DST starts on one of them, 49 hours when DST ends, and 48 hours otherwise.
"""

from datetime import UTC, date, datetime, time, timedelta
from typing import Final
from zoneinfo import ZoneInfo

from openadr3_client.oadr310.models.event.event import Event, ServerEvent
from pydantic_core import InitErrorDetails, PydanticCustomError

LOCAL_TIMEZONE: Final = ZoneInfo("Europe/Amsterdam")

COVERAGE_ERROR_MESSAGE: Final = (
    "The intervals of the event must together cover two full local calendar days, "
    "from 00:00 to 00:00 two days later (Europe/Amsterdam)."
)

type Span = tuple[datetime, datetime]


def two_day_window(first_day: date) -> tuple[datetime, datetime]:
    """Return the UTC span from local midnight at the start of `first_day` to local midnight two days later."""
    # Each end is anchored at its own local midnight; adding 48 hours to the start would be off by one
    # hour whenever a DST transition falls inside the window.
    start = datetime.combine(first_day, time(), LOCAL_TIMEZONE)
    end = datetime.combine(first_day + timedelta(days=2), time(), LOCAL_TIMEZONE)
    return start.astimezone(UTC), end.astimezone(UTC)


def _interval_spans(event: Event) -> list[Span]:
    """
    Return the span of each interval, or an empty list when the event is not cleanly continuous or separated.

    A missing or mixed interval definition is reported by the continuous-or-separated check, so it is not
    reported a second time as a coverage failure.
    """
    intervals = event.intervals or ()
    if not intervals:
        return []

    if event.interval_period is not None:
        if any(interval.interval_period is not None for interval in intervals):
            return []
        start = event.interval_period.start
        return [(start, start + len(intervals) * event.interval_period.duration)]

    periods = [interval.interval_period for interval in intervals]
    if any(period is None for period in periods):
        return []
    return [(period.start, period.start + period.duration) for period in periods if period is not None]


def _merge(spans: list[Span]) -> list[Span]:
    """Merge overlapping and touching spans into a time-ordered list of disjoint spans."""
    merged: list[Span] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


def _expected_window(event: Event, first_start: datetime) -> Span:
    """
    Return the window the event must cover.

    An event read back from the VTN carries its publication time, which fixes the window to the two days
    after it. A new event has no publication time yet, so its window is the two days starting on the local
    day of its first interval.
    """
    if isinstance(event, ServerEvent):
        published_on = event.created_date_time.astimezone(LOCAL_TIMEZONE).date()
        return two_day_window(published_on + timedelta(days=1))
    return two_day_window(first_start.astimezone(LOCAL_TIMEZONE).date())


def _covers_window(event: Event, spans: list[Span]) -> bool:
    """Return whether the spans, and the event duration when set, match the expected window exactly."""
    covered = _merge(spans)
    first_start = covered[0][0]
    window = _expected_window(event, first_start)

    # The event duration shortens or lengthens the span of the event, so when it is set the event only
    # covers the window if that span matches it as well.
    duration_matches = event.duration is None or (first_start, first_start + event.duration) == window

    return covered == [window] and duration_matches


def coverage_errors(event: Event) -> list[InitErrorDetails]:
    """Validate that the intervals of the event together cover exactly the expected two-day local window."""
    try:
        spans = _interval_spans(event)
        if not spans:
            return []
        covers = _covers_window(event, spans)
    except OverflowError:
        # OpenADR uses durations such as P9999Y to mean "repeat indefinitely", and adding one to a start
        # runs past datetime.max. Such a span cannot equal a two-day window, so it is a coverage failure.
        covers = False

    if covers:
        return []

    return [
        InitErrorDetails(
            type=PydanticCustomError("value_error", COVERAGE_ERROR_MESSAGE),
            loc=("intervals",),
            input=event.intervals,
            ctx={},
        )
    ]
