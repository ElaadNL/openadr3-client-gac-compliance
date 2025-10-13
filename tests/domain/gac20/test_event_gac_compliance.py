from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from openadr3_client.models.common.interval import Interval
from openadr3_client.models.common.interval_period import IntervalPeriod
from openadr3_client.models.common.target import Target
from openadr3_client.models.common.unit import Unit
from openadr3_client.models.event.event import NewEvent
from openadr3_client.models.event.event_payload import (
    EventPayload,
    EventPayloadDescriptor,
    EventPayloadType,
)
from openadr3_client.plugin import ValidatorPluginRegistry
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac20.plugin import Gac20ValidatorPlugin


def _default_valid_payload_descriptors() -> tuple[EventPayloadDescriptor, ...]:
    """Helper function to create a default payload descriptor that is GAC compliant."""
    return (EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KW),)


def _default_valid_targets() -> tuple[Target, ...]:
    """Helper function to create a default target that is GAC compliant."""
    return (
        Target(type="POWER_SERVICE_LOCATION", values=("EAN123456789012345",)),
        Target(type="VEN_NAME", values=("test-ven",)),
    )


def _create_event(
    intervals: tuple[Interval[EventPayload], ...],
    priority: int | None = None,
    targets: tuple[Target, ...] | None = _default_valid_targets(),
    payload_descriptors: tuple[EventPayloadDescriptor, ...] | None = _default_valid_payload_descriptors(),
    interval_period: IntervalPeriod | None = None,
) -> NewEvent:
    """
    Helper function to create a event with the specified values.

    Args:
        priority: The priority of the event.
        targets: The targets of the event.
        payload_descriptors: The payload descriptor of the event.
        interval_period: The interval period of the event.
        intervals: The intervals of the event.

    """
    return NewEvent(
        programID="test-program",
        event_name="test-event",
        priority=priority,
        targets=targets,
        payload_descriptors=payload_descriptors,
        interval_period=interval_period,
        intervals=intervals,
    )


@pytest.fixture(autouse=True)
def clear_plugins():
    """Clear plugins before each test and register GAC plugin."""
    ValidatorPluginRegistry.clear_plugins()
    ValidatorPluginRegistry.register_plugin(Gac20ValidatorPlugin.setup())
    yield
    ValidatorPluginRegistry.clear_plugins()


def test_continuous_interval_definition_valid() -> None:
    """
    Test that a continuous interval definition is valid.

    A Continious interval definition is when the interval_period is set on the event and implicitly
    applied to all intervals. Intervals cannot have their own interval_period set.
    """
    event = _create_event(
        interval_period=IntervalPeriod(
            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
            duration=timedelta(minutes=5),
        ),
        intervals=(
            Interval(
                id=0,
                interval_period=None,
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
            ),
            Interval(
                id=1,
                interval_period=None,
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)),),
            ),
        ),
    )

    assert event.interval_period is not None
    assert event.intervals[0].interval_period is None
    assert event.intervals[1].interval_period is None


def test_seperated_interval_definition_valid() -> None:
    """
    Test that a seperated interval definition is valid.

    A seperated interval definition is when the interval_period is not set on the event and
    must be explicitly set on all intervals.
    """
    event = _create_event(
        interval_period=None,
        intervals=(
            Interval(
                id=0,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                    duration=timedelta(minutes=5),
                ),
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
            ),
            Interval(
                id=1,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 5, 0, tzinfo=UTC),
                    duration=timedelta(minutes=5),
                ),
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)),),
            ),
        ),
    )

    assert event.interval_period is None
    assert event.intervals[0].interval_period is not None
    assert event.intervals[1].interval_period is not None


def test_combined_interval_definition_not_allowed() -> None:
    """
    Test to verify that a combined interval definition is not allowed.

    A combined interval definition is when the interval_period is set on the event and
    explicitly set on one or more intervals.
    """
    with pytest.raises(
        ValidationError,
        match="'interval_period' must either be set on the event-level, or for each interval.",
    ):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                Interval(
                    id=0,
                    interval_period=None,
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
                Interval(
                    id=1,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)),),
                ),
            ),
        )


def test_targets_compliant_valid() -> None:
    """
    Test that targets which are GAC compliant are accepted.

    GAC required targets are:
    - POWER_SERVICE_LOCATION
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
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                    duration=timedelta(minutes=5),
                ),
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
            ),
        ),
    )

    assert event.targets == gac_required_targets + additional_target


def test_missing_power_service_locations() -> None:
    """Test that missing POWER_SERVICE_LOCATION target raises an error."""
    ven_name_target_only = (Target(type="VEN_NAME", values=("test-ven",)),)

    with pytest.raises(
        ValidationError,
        match="The event must contain a POWER_SERVICE_LOCATION target.",
    ):
        _ = _create_event(
            targets=ven_name_target_only,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_missing_ven_name() -> None:
    """Test that missing VEN_NAME target raises an error."""
    power_service_locations_target_only = (Target(type="POWER_SERVICE_LOCATION", values=("EAN123456789012345",)),)

    with pytest.raises(ValidationError, match="The event must contain a VEN_NAME target."):
        _ = _create_event(
            targets=power_service_locations_target_only,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_multiple_power_service_location_targets() -> None:
    """Test that multiple POWER_SERVICE_LOCATION targets raises an error."""
    gac_required_targets = _default_valid_targets()
    additional_target = (Target(type="POWER_SERVICE_LOCATION", values=("test-target",)),)

    with pytest.raises(
        ValidationError,
        match="The event must contain exactly one POWER_SERVICE_LOCATION target.",
    ):
        _ = _create_event(
            targets=gac_required_targets + additional_target,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_multiple_ven_name_targets() -> None:
    """Test that multiple VEN_NAME targets raises an error."""
    gac_required_targets = _default_valid_targets()
    additional_target = (Target(type="VEN_NAME", values=("test-target",)),)

    with pytest.raises(ValidationError, match="The event must contain exactly one VEN_NAME target."):
        _ = _create_event(
            targets=gac_required_targets + additional_target,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_power_service_locations_target_value_empty() -> None:
    """Test that power_service_locations target with an empty value raises an error."""
    targets: tuple[Target, ...] = (
        Target(type="POWER_SERVICE_LOCATION", values=()),
        Target(type="VEN_NAME", values=("test-ven",)),
    )

    with pytest.raises(
        ValidationError,
        match="The POWER_SERVICE_LOCATION target value may not be empty.",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_power_service_locations_invalid_value_format() -> None:
    """Test that power_service_locations target without an EAN18 value raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATION", values=("invalid-value",)),
        Target(type="VEN_NAME", values=("test-ven",)),
    )

    with pytest.raises(
        ValueError,
        match="The POWER_SERVICE_LOCATION target value must be a list of 'EAN18' values.",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_ven_name_target_value_empty() -> None:
    """Test that VEN_NAME target with an empty value raises an error."""
    targets: tuple[Target, ...] = (
        Target(type="POWER_SERVICE_LOCATION", values=("EAN123456789012345",)),
        Target(type="VEN_NAME", values=()),
    )

    with pytest.raises(ValidationError, match="The VEN_NAME target value may not be empty."):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_ven_name_target_too_long() -> None:
    """Test that VEN_NAME target with a value longer than 128 characters raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATION", values=("EAN123456789012345",)),
        Target(type="VEN_NAME", values=("a" * 129,)),
    )

    with pytest.raises(
        ValueError,
        match="The VEN_NAME target value must be a list of 'VEN name' values",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_ven_name_target_too_short() -> None:
    """Test that VEN_NAME target with a value shorter than 1 character raises an error."""
    targets = (
        Target(type="POWER_SERVICE_LOCATION", values=("EAN123456789012345",)),
        Target(type="VEN_NAME", values=("",)),
    )

    with pytest.raises(
        ValidationError,
        match="The VEN_NAME target value must be a list of 'VEN name' values",
    ):
        _ = _create_event(
            targets=targets,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_no_payload_descriptors() -> None:
    """Test that an event with no payload descriptor raises an error."""
    with pytest.raises(ValueError, match="The event must have a payload descriptor."):
        _ = _create_event(
            payload_descriptors=None,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_multiple_payload_descriptors() -> None:
    """Test that an event with multiple payload descriptors raises an error."""
    with pytest.raises(ValidationError, match="The event must have exactly one payload descriptor."):
        _ = _create_event(
            payload_descriptors=(
                EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KW),
                EventPayloadDescriptor(payload_type=EventPayloadType.SIMPLE, units=Unit.KW),
            ),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_invalid_payload_type_in_descriptors() -> None:
    """Test that invalid payload type in descriptor raises an error."""
    with pytest.raises(
        ValidationError,
        match="The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'.",
    ):
        _ = _create_event(
            payload_descriptors=(EventPayloadDescriptor(payload_type=EventPayloadType.SIMPLE, units=Unit.KW),),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )


def test_invalid_unit_in_descriptors() -> None:
    """Test that invalid unit in descriptor raises an error."""
    with pytest.raises(ValidationError, match="The payload descriptor must have a units of 'KW'"):
        _ = _create_event(
            payload_descriptors=(
                EventPayloadDescriptor(payload_type=EventPayloadType.IMPORT_CAPACITY_LIMIT, units=Unit.KVA),
            ),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
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
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
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
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                    duration=timedelta(minutes=5),
                ),
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
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
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)),),
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
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.SIMPLE, values=(1.0,)),),
                ),
            ),
        )


def test_event_no_intervals() -> None:
    """Test that an event with no intervals raises an error."""
    with pytest.raises(ValueError, match="NewEvent must contain at least one interval"):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                duration=timedelta(minutes=5),
            ),
            intervals=(),
        )


def test_event_interval_no_payload() -> None:
    """Test that an event interval with no payload raises an error."""
    with pytest.raises(ValidationError, match="interval payload must contain at least one payload"):
        _ = _create_event(
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(),
                ),
            ),
        )


def test_event_interval_multiple_payloads() -> None:
    """Test that an event interval with multiple payloads raises an error."""
    with pytest.raises(ValidationError, match="The event interval must have exactly one payload."):
        _ = _create_event(
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(
                        EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),
                        EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(2.0,)),
                    ),
                ),
            ),
        )


def test_event_multiple_errors_grouped() -> None:
    """Test that multiple errors are grouped together and returned as a single error."""
    with pytest.raises(
        ValidationError,
        match="2 validation errors for NewEvent",
    ) as exc_info:
        _ = _create_event(
            targets=(),
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )

    grouped_errors = exc_info.value.errors()

    assert len(grouped_errors) == 2
    assert grouped_errors[0].get("type") == "value_error"
    assert grouped_errors[1].get("type") == "value_error"
    assert grouped_errors[0].get("msg") == "The event must contain a POWER_SERVICE_LOCATION target."
    assert grouped_errors[1].get("msg") == "The event must contain a VEN_NAME target."


def test_plugin_system_integration() -> None:
    """Test that the plugin system correctly integrates with the Event validation."""
    validators = ValidatorPluginRegistry.get_model_validators(NewEvent)
    assert len(validators) == 1

    valid_event = _create_event(
        intervals=(
            Interval(
                id=0,
                interval_period=IntervalPeriod(
                    start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                    duration=timedelta(minutes=5),
                ),
                payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
            ),
        ),
    )
    assert valid_event.event_name == "test-event"

    with pytest.raises(ValidationError) as exc_info:
        _create_event(
            targets=(),
            priority=5,
            interval_period=IntervalPeriod(
                start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                duration=timedelta(minutes=5),
            ),
            intervals=(
                Interval(
                    id=0,
                    interval_period=None,
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )

    errors = exc_info.value.errors()
    assert len(errors) == 3

    priority_error = errors[0]
    assert priority_error["loc"] == ("priority",)
    assert "priority" in priority_error["msg"]

    targets_error = errors[1]
    assert targets_error["loc"] == ("targets",)
    assert "POWER_SERVICE_LOCATION" in targets_error["msg"] or "VEN_NAME" in targets_error["msg"]

    targets_error = errors[2]
    assert targets_error["loc"] == ("targets",)
    assert "VEN_NAME" in targets_error["msg"]


def test_plugin_with_edge_cases() -> None:
    """Test plugin validation with various edge cases."""
    test_cases: list[tuple[str, dict[str, Any], int]] = [
        # description, kwargs, expected_error_count
        (
            "Priority + missing targets",
            {
                "priority": 5,
                "targets": (),
                "intervals": (
                    Interval(
                        id=0,
                        interval_period=IntervalPeriod(
                            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                            duration=timedelta(minutes=5),
                        ),
                        payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                    ),
                ),
            },
            3,  # priority + POWER_SERVICE_LOCATION + VEN_NAME
        ),
        (
            "Priority only",
            {
                "priority": 10,
                "intervals": (
                    Interval(
                        id=0,
                        interval_period=IntervalPeriod(
                            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                            duration=timedelta(minutes=5),
                        ),
                        payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                    ),
                ),
            },
            1,  # priority only
        ),
        (
            "Missing targets only",
            {
                "targets": (),
                "intervals": (
                    Interval(
                        id=0,
                        interval_period=IntervalPeriod(
                            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                            duration=timedelta(minutes=5),
                        ),
                        payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                    ),
                ),
            },
            2,  # POWER_SERVICE_LOCATION + VEN_NAME
        ),
        (
            "Missing POWER_SERVICE_LOCATION only",
            {
                "targets": (Target(type="VEN_NAME", values=("test-ven",)),),
                "intervals": (
                    Interval(
                        id=0,
                        interval_period=IntervalPeriod(
                            start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                            duration=timedelta(minutes=5),
                        ),
                        payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                    ),
                ),
            },
            1,  # POWER_SERVICE_LOCATION only
        ),
    ]

    for description, kwargs, expected_error_count in test_cases:
        with pytest.raises(ValidationError) as exc_info:
            _create_event(**kwargs)

        errors = exc_info.value.errors()
        assert len(errors) == expected_error_count, (
            f"Expected {expected_error_count} errors for '{description}'",
            f", got {len(errors)}: {[e['msg'] for e in errors]}",
        )


def test_plugin_error_details() -> None:
    """Test that plugin errors contain correct location and input information."""
    with pytest.raises(ValidationError) as exc_info:
        _create_event(
            targets=(),
            priority=10,
            interval_period=None,
            intervals=(
                Interval(
                    id=0,
                    interval_period=IntervalPeriod(
                        start=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
                        duration=timedelta(minutes=5),
                    ),
                    payloads=(EventPayload(type=EventPayloadType.IMPORT_CAPACITY_LIMIT, values=(1.0,)),),
                ),
            ),
        )

    errors = exc_info.value.errors()
    assert len(errors) == 3

    assert errors[0].get("type") == "value_error"
    assert errors[0].get("loc") == ("priority",)
    assert errors[0].get("input") == 10

    assert errors[1].get("type") == "value_error"
    assert errors[1].get("loc") == ("targets",)
    assert errors[1].get("input") == ()

    assert errors[2].get("type") == "value_error"
    assert errors[2].get("loc") == ("targets",)
    assert errors[2].get("input") == ()
