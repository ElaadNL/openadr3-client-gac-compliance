# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime, timedelta

import pytest
from openadr3_client._models.common.interval import Interval
from openadr3_client._models.common.interval_period import IntervalPeriod
from openadr3_client.oadr310.models.event.event import NewEvent
from openadr3_client.oadr310.models.event.event_payload import (
    EventPayload,
    EventPayloadDescriptor,
    EventPayloadType,
)
from openadr3_client.oadr310.models.unit import Unit
from pydantic import ValidationError

from tests.domain.gac22.factories import (
    ONE_HOUR,
    VALID_TARGET,
    continuous_event,
    icl_payload,
    separated_event,
)

START = datetime(2026, 1, 13, 23, 0, tzinfo=UTC)
ICL_DESCRIPTOR = EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KW)


def test_event_valid() -> None:
    """A continuous event with EAN-prefixed targets and a KW descriptor is accepted."""
    event = continuous_event(START, 48)

    assert event.targets == (VALID_TARGET,)


@pytest.mark.parametrize(
    "targets",
    [
        ("876543211234567890",),
        ("EAN" + "\N{ARABIC-INDIC DIGIT ONE}" * 18,),
        ("EAN87654321123456789",),
        ("ean876543211234567890",),
        (" EAN876543211234567890",),
        (),
        None,
    ],
    ids=["bare-digits", "arabic-indic", "ean-plus-17", "lowercase", "leading-space", "empty", "missing"],
)
def test_event_targets_invalid(targets: tuple[str, ...] | None) -> None:
    """Targets must be a non-empty list of EAN-prefixed grid connection identifiers."""
    with pytest.raises(ValidationError, match="grid connection identifiers"):
        continuous_event(START, 48, targets=targets)


def test_two_valid_descriptors_pass() -> None:
    """The event may carry more than one descriptor, as long as each is IMPORT_CAPACITY_LIMIT in KW."""
    event = continuous_event(START, 48, payload_descriptors=(ICL_DESCRIPTOR, ICL_DESCRIPTOR))

    assert event.payload_descriptors is not None
    assert len(event.payload_descriptors) == 2


def test_empty_descriptor_tuple_fails() -> None:
    """An empty descriptor tuple is a validation error rather than an IndexError."""
    with pytest.raises(ValidationError, match="at least one payload descriptor"):
        continuous_event(START, 48, payload_descriptors=())


def test_descriptor_wrong_units_fails() -> None:
    """Units must be KW; any other unit is rejected."""
    descriptor = EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KWH)

    with pytest.raises(ValidationError, match="units 'KW'"):
        continuous_event(START, 48, payload_descriptors=(descriptor,))


def test_price_descriptor_next_to_icl_fails() -> None:
    """A descriptor of another payload type is rejected, even next to a valid IMPORT_CAPACITY_LIMIT one."""
    price_descriptor = EventPayloadDescriptor(payload_type=EventPayloadType.PRICE, units=Unit.KWH)
    price = EventPayload(type=EventPayloadType.PRICE, values=(1.0,))
    intervals = tuple(Interval(id=i, payloads=(icl_payload(), price)) for i in range(48))

    with pytest.raises(ValidationError, match="Every payload descriptor must have payload type"):
        continuous_event(START, 48, intervals=intervals, payload_descriptors=(ICL_DESCRIPTOR, price_descriptor))


def test_misspelled_descriptor_next_to_icl_fails() -> None:
    """A misspelled payload type is not hidden by a valid IMPORT_CAPACITY_LIMIT descriptor next to it."""
    fields = continuous_event(START, 48).model_dump(by_alias=True, mode="json")
    fields["payloadDescriptors"] = [
        {"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "IMPORT_CAPACITY_LIMIT", "units": "KW"},
        {"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "IMPORT_CAP_LI", "units": "KW"},
    ]

    with pytest.raises(ValidationError, match="Every payload descriptor must have payload type"):
        NewEvent.model_validate(fields)


def test_single_non_icl_descriptor_fails() -> None:
    """Without an IMPORT_CAPACITY_LIMIT descriptor the event is rejected."""
    descriptor = EventPayloadDescriptor(payload_type=EventPayloadType.PRICE, units=Unit.KWH)

    with pytest.raises(ValidationError, match="payload type 'IMPORT_CAPACITY_LIMIT' and units 'KW'"):
        continuous_event(START, 48, payload_descriptors=(descriptor,))


def test_descriptor_lowercase_units_fails() -> None:
    """Units are case sensitive: 'kW' is not 'KW'."""
    fields = continuous_event(START, 48).model_dump(by_alias=True, mode="json")
    fields["payloadDescriptors"] = [
        {"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "IMPORT_CAPACITY_LIMIT", "units": "kW"}
    ]

    with pytest.raises(ValidationError, match="units 'KW'"):
        NewEvent.model_validate(fields)


def test_wrong_payload_type_in_first_interval_fails() -> None:
    """Every interval is checked, not just the last one."""
    intervals = (
        Interval(id=0, payloads=(EventPayload(type=EventPayloadType.PRICE, values=(1.0,)),)),
        *(Interval(id=i, payloads=(icl_payload(),)) for i in range(1, 48)),
    )

    with pytest.raises(ValidationError, match="payload of type 'IMPORT_CAPACITY_LIMIT'"):
        continuous_event(START, 48, intervals=intervals)


def test_extra_payload_next_to_icl_passes() -> None:
    """Other payloads next to the IMPORT_CAPACITY_LIMIT payload are allowed."""
    price = EventPayload(type=EventPayloadType.PRICE, values=(1.0,))
    intervals = tuple(Interval(id=i, payloads=(icl_payload(), price)) for i in range(48))

    event = continuous_event(START, 48, intervals=intervals)

    assert event.intervals is not None
    assert len(event.intervals[0].payloads) == 2


def test_several_values_per_payload_pass() -> None:
    """A payload may carry more than one value."""
    payload = EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(10, 8))
    intervals = tuple(Interval(id=i, payloads=(payload,)) for i in range(48))

    event = continuous_event(START, 48, intervals=intervals)

    assert event.intervals is not None
    assert event.intervals[0].payloads[0].values == (10, 8)


def test_priority_set_passes() -> None:
    """The specification does not forbid a priority."""
    event = continuous_event(START, 48, priority=0)

    assert event.priority == 0


def test_non_increasing_interval_ids_fail() -> None:
    """Interval ids must be strictly increasing."""
    intervals = tuple(Interval(id=i, payloads=(icl_payload(),)) for i in (0, 2, 1))

    with pytest.raises(ValidationError, match="strictly increasing"):
        continuous_event(START, 3, intervals=intervals)


def test_pure_continuous_passes() -> None:
    """Event-level interval period with none on the intervals is accepted."""
    event = continuous_event(START, 48)

    assert event.interval_period is not None


def test_pure_separated_passes() -> None:
    """Interval periods on every interval and none on the event is accepted."""
    event = separated_event([(START + i * ONE_HOUR, ONE_HOUR) for i in range(48)])

    assert event.interval_period is None


def test_mixed_event_period_and_interval_period_fails() -> None:
    """An event-level interval period excludes interval-level periods."""
    intervals = (
        Interval(
            id=0,
            interval_period=IntervalPeriod(start=START, duration=ONE_HOUR),
            payloads=(icl_payload(),),
        ),
    )

    with pytest.raises(ValidationError, match="'interval_period' must either be set"):
        continuous_event(START, 1, intervals=intervals)


def test_mixed_no_event_period_some_interval_periods_missing_fails() -> None:
    """Without an event-level period, every interval needs its own."""
    intervals = (
        Interval(
            id=0,
            interval_period=IntervalPeriod(start=START, duration=timedelta(hours=1)),
            payloads=(icl_payload(),),
        ),
        Interval(id=1, payloads=(icl_payload(),)),
    )

    with pytest.raises(ValidationError, match="'interval_period' must either be set"):
        separated_event([(START, ONE_HOUR)], intervals=intervals)
