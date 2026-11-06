# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""
Module which implements GAC 2.2 compliance validators for the event OpenADR3 types.

This module validates the constraints the Grid aware charging (GAC) specification places on a single
OpenADR3 event object: its targets, payload descriptors, interval definition and interval payloads.

Requirements that span more than one object, such as the presence of a program's events, cannot be
validated from the scope of a single event and are not checked here.
"""

from itertools import pairwise

from openadr3_client.oadr310.models.event.event import Event
from openadr3_client.oadr310.models.event.event_payload import EventPayloadType
from pydantic_core import InitErrorDetails, PydanticCustomError

from openadr3_client_gac_compliance.gac22.event_coverage import coverage_errors
from openadr3_client_gac_compliance.gac22.identifiers import is_grid_connection_identifier

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

    The targets must be a non-empty list of grid connection identifiers, each 'EAN' followed by 18 digits.
    """
    targets = self.targets

    if targets and all(is_grid_connection_identifier(target) for target in targets):
        return []

    return [
        InitErrorDetails(
            type=PydanticCustomError(
                "value_error",
                "The targets value must be a non-empty list of grid connection identifiers, "
                "each 'EAN' followed by 18 digits.",
            ),
            loc=("targets",),
            input=targets,
            ctx={},
        )
    ]


def _payload_descriptors_gac_compliant(
    self: Event,
) -> list[InitErrorDetails]:
    """
    Validates that the payload descriptors are GAC compliant.

    The following constraints are enforced for payload descriptors:

    - The event must have at least one payload descriptor.
    - Every descriptor must have payload type 'IMPORT_CAPACITY_LIMIT' and units 'KW' (case sensitive), the
      same way every interval must carry an 'IMPORT_CAPACITY_LIMIT' payload.
    """
    descriptors = self.payload_descriptors

    if not descriptors:
        return [
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The event must have at least one payload descriptor.",
                ),
                loc=("payload_descriptors",),
                input=descriptors,
                ctx={},
            )
        ]

    if all(d.payload_type == EventPayloadType.IMPORT_CAPACITY_LIMIT and d.units == "KW" for d in descriptors):
        return []

    return [
        InitErrorDetails(
            type=PydanticCustomError(
                "value_error",
                "Every payload descriptor must have payload type 'IMPORT_CAPACITY_LIMIT' and units 'KW' "
                "(case sensitive).",
            ),
            loc=("payload_descriptors",),
            input=descriptors,
            ctx={},
        )
    ]


def _event_interval_gac_compliant(self: Event) -> list[InitErrorDetails]:
    """
    Validates that the event intervals are GAC compliant.

    The following constraints are enforced for event intervals:

    - The event must have at least one interval.
    - The interval ids must be strictly increasing.
    - Every interval must include a payload of type 'IMPORT_CAPACITY_LIMIT'. Other payloads next to it,
      several values per payload and a priority on the event are all allowed.
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
        return validation_errors

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

    if not all(
        any(payload.type == EventPayloadType.IMPORT_CAPACITY_LIMIT for payload in interval.payloads)
        for interval in self.intervals
    ):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "Every interval must include a payload of type 'IMPORT_CAPACITY_LIMIT'.",
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

    - The event must have either a continuous or separated interval definition.
    - The intervals must together cover the two local calendar days after publication.
    """
    validation_errors: list[InitErrorDetails] = []

    errors = _continuous_or_separated(event)
    validation_errors.extend(errors)

    errors = coverage_errors(event)
    validation_errors.extend(errors)

    errors = _targets_compliant(event)
    validation_errors.extend(errors)

    errors = _payload_descriptors_gac_compliant(event)
    validation_errors.extend(errors)

    errors = _event_interval_gac_compliant(event)
    validation_errors.extend(errors)

    return validation_errors or None
