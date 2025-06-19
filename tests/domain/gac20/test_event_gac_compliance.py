from datetime import datetime, timedelta, timezone
import pytest

from typing import Tuple

from pydantic import ValidationError

from openadr3_client.models.common.interval_period import IntervalPeriod
from openadr3_client.models.event.event import NewEvent
from openadr3_client.models.event.event_payload import (
    EventPayload,
    EventPayloadType,
    EventPayloadDescriptor,
)
from openadr3_client.models.common.target import Target
from openadr3_client.models.common.interval import Interval


def _default_valid_payload_descriptor() -> Tuple[EventPayloadDescriptor, ...]:
    """Helper function to create a default payload descriptor that is GAC compliant."""
    return (
        EventPayloadDescriptor(
            payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units="KW"
        ),
    )


def _default_valid_targets() -> Tuple[Target, ...]:
    """Helper function to create a default target that is GAC compliant."""
    return (
        Target(type="POWER_SERVICE_LOCATIONS", values=("123456789012345678",)),
        Target(type="VEN_NAME", values=("test-ven",)),
    )


def _create_event(
    intervals: Tuple[Interval[EventPayload], ...],
    priority: int | None = None,
    targets: Tuple[Target, ...] | None = _default_valid_targets(),
    payload_descriptor: Tuple[EventPayloadDescriptor, ...]
    | None = _default_valid_payload_descriptor(),
    interval_period: IntervalPeriod | None = None,
) -> NewEvent:
    """Helper function to create a event with the specified values.

    Args:
        priority: The priority of the event.
        targets: The targets of the event.
        payload_descriptor: The payload descriptor of the event.
        interval_period: The interval period of the event.
        intervals: The intervals of the event.
    """
    return NewEvent(
        id=None,
        programID="test-program",
        event_name="test-event",
        priority=priority,
        targets=targets,
        payload_descriptor=payload_descriptor,
        interval_period=interval_period,
        intervals=intervals,
    )


def test_continuous_interval_definition_valid() -> None:
    """Test that a continuous interval definition is valid.

    A Continious interval definition is when the interval_period is set on the event and implicitly
    applied to all intervals. Intervals cannot have their own interval_period set.
    """
    event = _create_event(
        interval_period=IntervalPeriod(
            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            duration=timedelta(minutes=5),
        ),
        intervals=(
            Interval(
                id=0,
                interval_period=None,
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                    ),
                ),
            ),
            Interval(
                id=1,
                interval_period=None,
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)
                    ),
                ),
            ),
        ),
    )

    assert event.interval_period is not None
    assert event.intervals[0].interval_period is None
    assert event.intervals[1].interval_period is None


def test_seperated_interval_definition_valid() -> None:
    """Test that a seperated interval definition is valid.

    A seperated interval definition is when the interval_period is not set on the event and
    must be explicitly set on all intervals.
    """
    event = _create_event(
        interval_period=None,
        intervals=(
            Interval(
                id=0,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    duration=timedelta(minutes=5),
                ),
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                    ),
                ),
            ),
            Interval(
                id=1,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 5, 0, tzinfo=timezone.utc),
                    duration=timedelta(minutes=5),
                ),
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)
                    ),
                ),
            ),
        ),
    )

    assert event.interval_period is None
    assert event.intervals[0].interval_period is not None
    assert event.intervals[1].interval_period is not None


def test_combined_interval_definition_not_allowed() -> None:
    """Test to verify that a combined interval definition is not allowed.

    A combined interval definition is when the interval_period is set on the event and
    explicitly set on one or more intervals.
    """
    with pytest.raises(
        ValidationError,
        match="Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'.",
    ):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                Interval(
                    id=0,
                    interval_period=None,
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
                Interval(
                    id=1,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)
                        ),
                    ),
                ),
            ),
        )


def test_targets_compliant_valid() -> None:
    """Test that targets which are GAC compliant are accepted.

    GAC required targets are:
    - POWER_SERVICE_LOCATIONS
    - VEN_NAME

    Additional targets are allowed, but these two must be present.
    """
    gac_required_targets = _default_valid_targets()
    additional_target = (Target(type="CUSTOM_TARGET", values=("test-target",)),)

    event = _create_event(
        targets=gac_required_targets + additional_target,
        interval_period=None,
        intervals=(
            Interval(
                id=0,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    duration=timedelta(minutes=5),
                ),
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                    ),
                ),
            ),
        ),
    )

    assert event.targets == gac_required_targets + additional_target


def test_missing_power_service_locations() -> None:
    """Test that missing POWER_SERVICE_LOCATIONS target raises an error."""
    ven_name_target_only = (Target(type="VEN_NAME", values=("test-ven",)),)

    with pytest.raises(
        ValidationError,
        match="The event must contain a POWER_SERVICE_LOCATIONS target.",
    ):
        _ = _create_event(
            targets=ven_name_target_only,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_missing_ven_name() -> None:
    """Test that missing VEN_NAME target raises an error."""
    power_service_locations_target_only = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("123456789012345678",)),
    )

    with pytest.raises(
        ValidationError, match="The event must contain a VEN_NAME target."
    ):
        _ = _create_event(
            targets=power_service_locations_target_only,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_multiple_power_service_location_targets() -> None:
    """Test that multiple POWER_SERVICE_LOCATIONS targets raises an error."""
    gac_required_targets = _default_valid_targets()
    additional_target = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("test-target",)),
    )

    with pytest.raises(
        ValidationError,
        match="The event must contain exactly one POWER_SERVICE_LOCATIONS target.",
    ):
        _ = _create_event(
            targets=gac_required_targets + additional_target,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_multiple_ven_name_targets() -> None:
    """Test that multiple VEN_NAME targets raises an error."""
    gac_required_targets = _default_valid_targets()
    additional_target = (Target(type="VEN_NAME", values=("test-target",)),)

    with pytest.raises(
        ValidationError, match="The event must contain only one VEN_NAME target."
    ):
        _ = _create_event(
            targets=gac_required_targets + additional_target,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_power_service_locations_target_value_empty() -> None:
    """Test that power_service_locations target with an empty value raises an error."""
    targets: Tuple[Target, ...] = (
        Target(type="POWER_SERVICE_LOCATIONS", values=()),
        Target(type="VEN_NAME", values=("test-ven",)),
    )

    with pytest.raises(
        ValidationError,
        match="The POWER_SERVICE_LOCATIONS target value cannot be empty.",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_power_service_locations_invalid_value_format() -> None:
    """Test that power_service_locations target without an EAN18 value raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("invalid-value",)),
        Target(type="VEN_NAME", values=("test-ven",)),
    )

    with pytest.raises(
        ValueError,
        match="The POWER_SERVICE_LOCATIONS target value must be a list of 'EAN18' values.",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_ven_name_target_value_empty() -> None:
    """Test that VEN_NAME target with an empty value raises an error."""
    targets: Tuple[Target, ...] = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("123456789012345678",)),
        Target(type="VEN_NAME", values=()),
    )

    with pytest.raises(
        ValidationError, match="The VEN_NAME target value cannot be empty."
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_ven_name_target_too_long() -> None:
    """Test that VEN_NAME target with a value longer than 128 characters raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("123456789012345678",)),
        Target(type="VEN_NAME", values=("a" * 129,)),
    )

    with pytest.raises(
        ValueError,
        match="The VEN_NAME target value must be a list of 'ven object name' values",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_ven_name_target_too_short() -> None:
    """Test that VEN_NAME target with a value shorter than 1 character raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATIONS", values=("123456789012345678",)),
        Target(type="VEN_NAME", values=("",)),
    )

    with pytest.raises(
        ValidationError,
        match="The VEN_NAME target value must be a list of 'ven object name' values",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_no_payload_descriptor() -> None:
    """Test that an event with no payload descriptor raises an error."""
    with pytest.raises(ValueError, match="The event must have a payload descriptor."):
        _ = _create_event(
            payload_descriptor=None,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_multiple_payload_descriptors() -> None:
    """Test that an event with multiple payload descriptors raises an error."""
    with pytest.raises(
        ValidationError, match="The event must have exactly one payload descriptor."
    ):
        _ = _create_event(
            payload_descriptor=(
                EventPayloadDescriptor(
                    payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units="KW"
                ),
                EventPayloadDescriptor(
                    payload_type=EventPayloadType.SIMPLE, units="test"
                ),
            ),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_invalid_payload_type_in_descriptor() -> None:
    """Test that invalid payload type in descriptor raises an error."""
    with pytest.raises(
        ValidationError,
        match="The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'.",
    ):
        _ = _create_event(
            payload_descriptor=(
                EventPayloadDescriptor(
                    payload_type=EventPayloadType.SIMPLE, units="KW"
                ),
            ),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_invalid_unit_in_descriptor() -> None:
    """Test that invalid unit in descriptor raises an error."""
    with pytest.raises(
        ValidationError, match="The payload descriptor must have a units of 'KW'"
    ):
        _ = _create_event(
            payload_descriptor=(
                EventPayloadDescriptor(
                    payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units="kw"
                ),
            ),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_priority_set() -> None:
    """Test that a priority that is set raises an error for GAC 2.0 compliance."""
    with pytest.raises(
        ValidationError,
        match="The event must not have a priority set for GAC 2.0 compliance",
    ):
        _ = _create_event(
            priority=1,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
            ),
        )


def test_priority_not_set() -> None:
    """Test that a priority that is not set is valid for GAC 2.0 compliance."""
    _ = _create_event(
        priority=None,
        interval_period=None,
        intervals=(
            Interval(
                id=0,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    duration=timedelta(minutes=5),
                ),
                payloads=(
                    EventPayload(
                        type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                    ),
                ),
            ),
        ),
    )


def test_non_increasing_interval_ids() -> None:
    """Test that non-increasing interval IDs raises an error."""
    with pytest.raises(
        ValidationError,
        match="The event interval must have an id value that is strictly increasing.",
    ):
        _ = _create_event(
            interval_period=None,
            intervals=(
                Interval(
                    id=1,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                    ),
                ),
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)
                        ),
                    ),
                ),
            ),
        )


def test_interval_payload_type_invalid() -> None:
    """Test that an invalid payload type in an interval payload raises an error."""
    with pytest.raises(
        ValidationError,
        match="The event interval payload must have a payload type of 'IMPORT_CAPACITY_LIMIT'.",
    ):
        _ = _create_event(
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(type=EventPayloadType.SIMPLE, values=(1.0,)),
                    ),
                ),
            ),
        )


def test_event_no_intervals() -> None:
    """Test that an event with no intervals raises an error."""
    with pytest.raises(ValueError, match="NewEvent must contain at least one interval"):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                duration=timedelta(minutes=5),
            ),
            intervals=(),
        )


def test_event_interval_no_payload() -> None:
    """Test that an event interval with no payload raises an error."""
    with pytest.raises(
        ValidationError, match="interval payload must contain at least one payload"
    ):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(),
                ),
            ),
        )


def test_event_interval_multiple_payloads() -> None:
    """Test that an event interval with multiple payloads raises an error."""
    with pytest.raises(
        ValidationError, match="The event interval must have exactly one payload."
    ):
        _ = _create_event(
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)
                        ),
                        EventPayload(
                            type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)
                        ),
                    ),
                ),
            ),
        )
