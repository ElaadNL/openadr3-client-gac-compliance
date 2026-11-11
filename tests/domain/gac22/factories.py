# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta
from typing import Any

from openadr3_client._models.common.interval import Interval
from openadr3_client._models.common.interval_period import IntervalPeriod
from openadr3_client.oadr310.models.event.event import ExistingEvent, NewEvent
from openadr3_client.oadr310.models.event.event_payload import (
    EventPayload,
    EventPayloadDescriptor,
    EventPayloadType,
)
from openadr3_client.oadr310.models.unit import Unit

VALID_TARGET = "EAN876543211234567890"
ONE_HOUR = timedelta(hours=1)


def icl_payload(value: float = 1.0) -> EventPayload:
    """An IMPORT_CAPACITY_LIMIT payload with a single value."""
    return EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(value,))


def _event(**fields: Any) -> NewEvent:  # noqa: ANN401
    defaults: dict[str, Any] = {
        "programID": "test-program",
        "event_name": "test-event",
        "targets": (VALID_TARGET,),
        "payload_descriptors": (
            EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KW),
        ),
    }
    return NewEvent(**{**defaults, **fields})


def continuous_event(start: datetime, hours: int, **overrides: Any) -> NewEvent:  # noqa: ANN401
    """An event with one event-level interval period and `hours` consecutive PT1H intervals."""
    return _event(
        **{
            "interval_period": IntervalPeriod(start=start, duration=ONE_HOUR),
            "intervals": tuple(Interval(id=i, payloads=(icl_payload(),)) for i in range(hours)),
            **overrides,
        }
    )


def separated_event(spans: list[tuple[datetime, timedelta]], **overrides: Any) -> NewEvent:  # noqa: ANN401
    """An event without an event-level interval period, where each interval carries its own span."""
    intervals = tuple(
        Interval(
            id=i,
            interval_period=IntervalPeriod(start=start, duration=duration),
            payloads=(icl_payload(),),
        )
        for i, (start, duration) in enumerate(spans)
    )
    return _event(**{"interval_period": None, "intervals": intervals, **overrides})


def existing_event(start: datetime, hours: int, created: datetime) -> ExistingEvent:
    """A continuous event as the VTN returns it, published at `created`."""
    event = continuous_event(start, hours)
    return ExistingEvent(
        **event.model_dump(by_alias=True),
        id="test-event-id",
        created_date_time=created,
        modification_date_time=created,
    )
