"""
Module which implements GAC compliance validators for the event OpenADR3 types.

This module validates all the object constraints and requirements on the OpenADR3 events resource
as specified in the Grid aware charging (GAC) specification.

There is one requirement that is not validated here, as it cannot be validated through the scope of the
pydantic validators. Namely, the requirement that a safe mode event MUST be present in a program.

As the pydantic validator works on the scope of a single Event Object, it is not possible to validate
that a safe mode event is present in a program. And it cannot be validated on the Program object,
as the program object does not contain the events, these are stored separately in the VTN.
"""

import re
from itertools import pairwise

from openadr3_client.models.event.event import Event
from openadr3_client.models.event.event_payload import EventPayloadType
from pydantic_core import InitErrorDetails, PydanticCustomError

INTERVAL_PERIOD_ERROR_MESSAGE = "'interval_period' must either be set on the event-level, or for each interval."


def _continuous_or_separated(self: Event) -> list[InitErrorDetails]:
    """
    Validates that events have consistent interval definitions GAC compliant.

    The Grid aware charging (GAC) specification allows for two types of (mutually exclusive)
    interval definitions:

    1. Continuous
    2. Separated

    The continuous implementation can be used when all intervals have the same duration.
    In this case, only the top-level intervalPeriod of the event may be used, and the intervalPeriods
    of the individual intervals must be None.

    In the separated implementation, the intervalPeriods must be set on each individual intervals,
    and the top-level intervalPeriod of the event must be None. This separated implementation allows events to have differing
    durations.
    """  # noqa: E501
    validation_errors: list[InitErrorDetails] = []

    intervals = self.intervals or ()

    if self.interval_period is None:
        # interval period not set at top level of the event.
        # Ensure that all intervals have the interval_period defined, to comply with the GAC specification.
        undefined_intervals_period = [i for i in intervals if i.interval_period is None]
        if undefined_intervals_period:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        INTERVAL_PERIOD_ERROR_MESSAGE,
                    ),
                    loc=("intervals",),
                    input=self.intervals,
                    ctx={},
                )
            )
    else:
        # interval period set at top level of the event.
        # Ensure that all intervals do not have the interval_period defined, to comply with the GAC specification.
        duplicate_interval_period = [i for i in intervals if i.interval_period is not None]
        if duplicate_interval_period:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        INTERVAL_PERIOD_ERROR_MESSAGE,
                    ),
                    loc=("intervals",),
                    input=self.intervals,
                    ctx={},
                )
            )

    return validation_errors


def _targets_compliant(self: Event) -> list[InitErrorDetails]:
    """
    Validates that the targets of the event are GAC compliant.

    The following constraints are enforced for targets:

    - The event must contain a POWER_SERVICE_LOCATION target.
    - The POWER_SERVICE_LOCATION target value must be a list of 'EAN18' values.
    - The event must contain a VEN_NAME target.
    - The VEN_NAME target value must be a list of 'VEN name' values (between 1 and 128 characters).
    """
    validation_errors: list[InitErrorDetails] = []
    targets = self.targets or ()

    power_service_locations = [t for t in targets if t.type == "POWER_SERVICE_LOCATION"]
    ven_names = [t for t in targets if t.type == "VEN_NAME"]

    if not power_service_locations:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must contain a POWER_SERVICE_LOCATION target.",
                ),
                loc=("targets",),
                input=self.targets,
                ctx={},
            )
        )

    if not ven_names:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must contain a VEN_NAME target.",
                ),
                loc=("targets",),
                input=self.targets,
                ctx={},
            )
        )

    if len(power_service_locations) > 1:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must contain exactly one POWER_SERVICE_LOCATION target.",
                ),
                loc=("targets",),
                input=self.targets,
                ctx={},
            )
        )

    if len(ven_names) > 1:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must contain exactly one VEN_NAME target.",
                ),
                loc=("targets",),
                input=self.targets,
                ctx={},
            )
        )

    if power_service_locations and ven_names and len(power_service_locations) == 1 and len(ven_names) == 1:
        power_service_location = power_service_locations[0]
        ven_name = ven_names[0]

        if len(power_service_location.values) == 0:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The POWER_SERVICE_LOCATION target value may not be empty.",
                    ),
                    loc=("targets",),
                    input=self.targets,
                    ctx={},
                )
            )

        if not all(re.fullmatch(r"^\d{18}$", v) for v in power_service_location.values):
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The POWER_SERVICE_LOCATION target value must be a list of 'EAN18' values.",
                    ),
                    loc=("targets",),
                    input=self.targets,
                    ctx={},
                )
            )

        if len(ven_name.values) == 0:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The VEN_NAME target value may not be empty.",
                    ),
                    loc=("targets",),
                    input=self.targets,
                    ctx={},
                )
            )

        if not all(1 <= len(v) <= 128 for v in ven_name.values):  # noqa: PLR2004
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The VEN_NAME target value must be a list of 'VEN name' values (between 1 and 128 characters).",
                    ),
                    loc=("targets",),
                    input=self.targets,
                    ctx={},
                )
            )

    return validation_errors


def _payload_descriptors_gac_compliant(
    self: Event,
) -> list[InitErrorDetails]:
    """
    Validates that the payload descriptor is GAC compliant.

    The following constraints are enforced for payload descriptors:

    - The event interval must contain exactly one payload descriptor.
    - The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'
    - The payload descriptor must have a units of 'KW' (case sensitive).
    """
    validation_errors: list[InitErrorDetails] = []

    if self.payload_descriptors is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must have a payload descriptor.",
                ),
                loc=("payload_descriptors",),
                input=self.payload_descriptors,
                ctx={},
            )
        )

    if self.payload_descriptors is not None:
        if len(self.payload_descriptors) != 1:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The event must have exactly one payload descriptor.",
                    ),
                    loc=("payload_descriptors",),
                    input=self.payload_descriptors,
                    ctx={},
                )
            )

        payload_descriptors = self.payload_descriptors[0]

        if payload_descriptors.payload_type != EventPayloadType.IMPORT_CAPACITY_LIMIT:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The payload descriptor must have a payload type of 'IMPORT_CAPACITY_LIMIT'.",
                    ),
                    loc=("payload_descriptors",),
                    input=self.payload_descriptors,
                    ctx={},
                )
            )

        if payload_descriptors.units != "KW":
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The payload descriptor must have a units of 'KW' (case sensitive).",
                    ),
                    loc=("payload_descriptors",),
                    input=self.payload_descriptors,
                    ctx={},
                )
            )

    return validation_errors


def _event_interval_gac_compliant(self: Event) -> list[InitErrorDetails]:
    """
    Validates that the event interval is GAC compliant.

    The following constraints are enforced for event intervals:

    - The event interval must have an id value that is strictly increasing.
    - The event interval must have exactly one payload.
    - The payload of the event interval must have a type of 'IMPORT_CAPACITY_LIMIT'
    """
    validation_errors: list[InitErrorDetails] = []

    if not self.intervals:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must have at least one interval.",
                ),
                loc=("intervals",),
                input=self.intervals,
                ctx={},
            )
        )

    if not all(curr.id > prev.id for prev, curr in pairwise(self.intervals)):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event interval must have an id value that is strictly increasing.",
                ),
                loc=("intervals",),
                input=self.intervals,
                ctx={},
            )
        )

    for interval in self.intervals:
        if interval.payloads is None:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The event interval must have a payload.",
                    ),
                    loc=("intervals",),
                    input=self.intervals,
                    ctx={},
                )
            )

        if len(interval.payloads) != 1:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The event interval must have exactly one payload.",
                    ),
                    loc=("intervals",),
                    input=self.intervals,
                    ctx={},
                )
            )
        else:
            payload = interval.payloads[0]

            if payload.type != EventPayloadType.IMPORT_CAPACITY_LIMIT:
                validation_errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError(
                            "value_error",
                            "The event interval payload must have a payload type of 'IMPORT_CAPACITY_LIMIT'.",
                        ),
                        loc=("intervals",),
                        input=self.intervals,
                        ctx={},
                    )
                )
            if len(payload.values) > 1:
                validation_errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError(
                            "value_error",
                            "The event interval payload must have exactly one value per payload.",
                        ),
                        loc=("intervals",),
                        input=self.intervals,
                        ctx={},
                    )
                )

    return validation_errors


def validate_event_gac_compliant(event: Event) -> list[InitErrorDetails] | None:
    """
    Validates that events are GAC compliant.

    The following constraints are enforced for events:

    - The event must not have a priority set.
    - The event must have either a continuous or separated interval definition.
    """
    validation_errors: list[InitErrorDetails] = []

    if event.priority is not None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must not have a priority set for GAC 2.0 compliance",
                ),
                loc=("priority",),
                input=event.priority,
                ctx={},
            )
        )

    errors = _continuous_or_separated(event)
    validation_errors.extend(errors)

    errors = _targets_compliant(event)
    validation_errors.extend(errors)

    errors = _payload_descriptors_gac_compliant(event)
    validation_errors.extend(errors)

    errors = _event_interval_gac_compliant(event)
    validation_errors.extend(errors)

    return validation_errors if validation_errors else None
