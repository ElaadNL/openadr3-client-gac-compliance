from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
import pytest

from openadr3_client_gac_compliance import *
from openadr3_client.domain.common.interval_period import IntervalPeriod
from openadr3_client.domain.event.event import NewEvent
from openadr3_client.domain.event.event_interval import EventInterval
from openadr3_client.domain.event.event_payload import EventPayload, EventPayloadType

def test_event_no_intervals_defined() -> None:
    with pytest.raises(
        ValidationError,
        match="Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'.",
    ):
        _ = NewEvent(
            id=None,
            programID="test-program",
            event_name=None,
            priority=None,
            targets=(),
            payload_descriptor=(),
            interval_period=None,
            intervals=(
                EventInterval(
                    id=0,
                    interval_period=None,
                    payloads=(
                        EventPayload(type=EventPayloadType.SIMPLE, values=(2.0, 3.0)),
                    ),
                ),
            ),
        )


def test_event_duplicate_intervals_defined() -> None:
    with pytest.raises(
        ValidationError,
        match="Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'.",
    ):
        _ = NewEvent(
            id=None,
            programID="test-program",
            event_name=None,
            priority=None,
            targets=(),
            payload_descriptor=(),
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                EventInterval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(type=EventPayloadType.SIMPLE, values=(2.0, 3.0)),
                    ),
                ),
            ),
        )