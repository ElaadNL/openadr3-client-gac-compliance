"""Module which implements GAC compliance validators for the event OpenADR3 types.

This module validates all the object constraints and requirements on the OpenADR3 events resource
as specified in the Grid aware charging (GAC) specification.

There is one requirement that is not validated here, as it cannot be validated through the scope of the
pydantic validators. Namely, the requirement that a safe mode event MUST be present in a program.

As the pydantic validator works on the scope of a single Event Object, it is not possible to validate
that a safe mode event is present in a program. And it cannot be validated on the Program object,
as the program object does not contain the events, these are stored seperately in the VTN.
"""

from itertools import pairwise
import re
from openadr3_client.models.model import ValidatorRegistry, Model as ValidatorModel
from openadr3_client.models.event.event import Event
from openadr3_client.models.event.event_payload import EventPayloadType


def _continuous_or_seperated(self: Event) -> Event:
    """Enforces that events either have consistent interval definitions compliant with GAC.

    the Grid aware charging (GAC) specification allows for two types of (mutually exclusive)
    interval definitions:

    1. Continuous
    2. Seperated

    The continious implementation can be used when all intervals have the same duration.
    In this case, only the top-level intervalPeriod of the event can be used, and the intervalPeriods
    of the individual intervals must be None.

    In the seperated intervalDefinition approach, the intervalPeriods must be set on each individual intervals,
    and the top-level intervalPeriod of the event must be None. This seperated approach is used when events have differing
    durations.
    """
    intervals = self.intervals or ()

    if self.interval_period is None:
        # interval period not set at top level of the event.
        # Ensure that all intervals have the interval_period defined, to comply with the GAC specification.
        undefined_intervals_period = [i for i in intervals if i.interval_period is None]
        if undefined_intervals_period:
            raise ValueError(
                "Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'."
            )
    else:
        # interval period set at top level of the event.
        # Ensure that all intervals do not have the interval_period defined, to comply with the GAC specification.
        duplicate_interval_period = [
            i for i in intervals if i.interval_period is not None
        ]
        if duplicate_interval_period:
            raise ValueError(
                "Either 'interval_period' must be set on the event once, or every interval must have its own 'interval_period'."
            )

    return self


def _targets_compliant(self: Event) -> Event:
    """Enforces that the targets of the event are compliant with GAC.

    GAC enforces the following constraints for targets:

    - The event must contain a POWER_SERVICE_LOCATIONS target.
    - The POWER_SERVICE_LOCATIONS target value must be a list of 'EAN18' values.
    - The event must contain a VEN_NAME target.
    - The VEN_NAME target value must be a list of 'ven object name' values (between 1 and 128 characters).
    """
    targets = self.targets or ()

    power_service_locations = [
        t for t in targets if t.type == "POWER_SERVICE_LOCATIONS"
    ]
    ven_names = [t for t in targets if t.type == "VEN_NAME"]

    if not power_service_locations:
        raise ValueError("The event must contain a POWER_SERVICE_LOCATIONS target.")

    if not ven_names:
        raise ValueError("The event must contain a VEN_NAME target.")

    if len(power_service_locations) > 1:
        raise ValueError(
            "The event must contain exactly one POWER_SERVICE_LOCATIONS target."
        )

    if len(ven_names) > 1:
        raise ValueError("The event must contain only one VEN_NAME target.")

    power_service_location = power_service_locations[0]
    ven_name = ven_names[0]

    if len(power_service_location.values) == 0:
        raise ValueError("The POWER_SERVICE_LOCATIONS target value cannot be empty.")

    if not all(re.fullmatch(r"\d{18}", v) for v in power_service_location.values):
        raise ValueError(
            "The POWER_SERVICE_LOCATIONS target value must be a list of 'EAN18' values."
        )

    if len(ven_name.values) == 0:
        raise ValueError("The VEN_NAME target value cannot be empty.")

    if not all(1 <= len(v) <= 128 for v in ven_name.values):
        raise ValueError(
            "The VEN_NAME target value must be a list of 'ven object name' values (between 1 and 128 characters)."
        )

    return self


def _payload_descriptor_gac_compliant(self: Event) -> Event:
    """Enforces that the payload descriptor is GAC compliant.

    GAC enforces the following constraints for payload descriptors:

    - The event interval must exactly one payload descriptor.
    - The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'
    - The payload descriptor must have a units of 'KW' (case sensitive).
    """
    if self.payload_descriptor is None:
        raise ValueError("The event must have a payload descriptor.")

    if len(self.payload_descriptor) != 1:
        raise ValueError("The event must have exactly one payload descriptor.")

    payload_descriptor = self.payload_descriptor[0]

    if payload_descriptor.payload_type != EventPayloadType.IMPORT_CAPACITY_LIMIT:
        raise ValueError(
            "The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'."
        )

    if payload_descriptor.units != "KW":
        raise ValueError(
            "The payload descriptor must have a units of 'KW' (case sensitive)."
        )

    return self


def _event_interval_gac_compliant(self: Event) -> Event:
    """Enforces that the event interval is GAC compliant.

    GAC enforces the following constraints for event intervals:

    - The event interval must have an id value that is strictly increasing.
    - The event interval must have exactly one payload.
    - The payload of the event interval must have a type of 'IMPORT_CAPACITY_LIMIT'
    """
    if not self.intervals:
        raise ValueError("The event must have at least one interval.")

    if not all(curr.id > prev.id for prev, curr in pairwise(self.intervals)):
        raise ValueError(
            "The event interval must have an id value that is strictly increasing."
        )

    for interval in self.intervals:
        if interval.payloads is None:
            raise ValueError("The event interval must have a payload.")

        if len(interval.payloads) != 1:
            raise ValueError("The event interval must have exactly one payload.")

        payload = interval.payloads[0]

        if payload.type != EventPayloadType.IMPORT_CAPACITY_LIMIT:
            raise ValueError(
                "The event interval payload must have a payload type of 'IMPORT_CAPACITY_LIMIT'."
            )

    return self


@ValidatorRegistry.register(Event, ValidatorModel())
def event_gac_compliant(self: Event) -> Event:
    """Enforces that events are GAC compliant.

    GAC enforces the following constraints for events:

    - The event must have a priority set.
    - The priority must be greater than or equal to 0 and less than or equal to 999.
    - The event must have either a continuous or seperated interval definition.
    """
    if self.priority is None:
        raise ValueError("The event must have a priority set.")

    if self.priority > 999:
        raise ValueError(
            "The priority must be greater than or equal to 0 and less than or equal to 999."
        )

    interval_periods_validated = _continuous_or_seperated(self)
    targets_validated = _targets_compliant(interval_periods_validated)
    payload_descriptor_validated = _payload_descriptor_gac_compliant(targets_validated)
    event_interval_validated = _event_interval_gac_compliant(
        payload_descriptor_validated
    )

    return event_interval_validated
