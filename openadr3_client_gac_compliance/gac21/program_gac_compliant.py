# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""Module which implements GAC 2.1 compliance validators for the program OpenADR3 types."""

import re

from openadr3_client.oadr310.models.program.program import Program
from openadr3_client.oadr310.models.program.program_attribute import ProgramAttributeType
from pydantic_core import InitErrorDetails, PydanticCustomError


def validate_program_gac_compliant(program: Program) -> list[InitErrorDetails] | None:
    """
    Validates that the program is GAC compliant.

    The following constraints are enforced for programs (all in the `attributes` field):
    - The program must have a `RETAILER_NAME` attribute.
    - The `RETAILER_NAME` value must be between 2 and 128 characters long.
    - The program MUST have a `PROGRAM_TYPE` attribute.
    - The `PROGRAM_TYPE` value MUST equal "DSO_CPO_INTERFACE-2.1.1".
    - The program MUST have a `BINDING_EVENTS` attribute set to true.

    """
    validation_errors: list[InitErrorDetails] = []

    program_type_regex = r"^DSO_CPO_INTERFACE-2\.1\.1$"

    attributes = program.attributes

    retailer_name_attr = attributes.get_by_type(ProgramAttributeType.RETAILER_NAME) if attributes else None
    if retailer_name_attr is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a RETAILER_NAME attribute.",
                ),
                loc=("attributes",),
                input=program.attributes,
                ctx={},
            )
        )
    else:
        retailer_name = retailer_name_attr.values[0] if retailer_name_attr.values else None
        if retailer_name is None or len(str(retailer_name)) < 2 or len(str(retailer_name)) > 128:  # noqa: PLR2004
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The RETAILER_NAME attribute must be between 2 and 128 characters long.",
                    ),
                    loc=("attributes",),
                    input=program.attributes,
                    ctx={},
                )
            )

    program_type_attr = attributes.get_by_type(ProgramAttributeType.PROGRAM_TYPE) if attributes else None
    if program_type_attr is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a PROGRAM_TYPE attribute.",
                ),
                loc=("attributes",),
                input=program.attributes,
                ctx={},
            )
        )
    else:
        program_type = program_type_attr.values[0] if program_type_attr.values else None
        if program_type is None or not re.fullmatch(program_type_regex, str(program_type)):
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.1.1.",
                    ),
                    loc=("attributes",),
                    input=program.attributes,
                    ctx={},
                )
            )

    binding_events_attr = attributes.get_by_type(ProgramAttributeType.BINDING_EVENTS) if attributes else None
    if binding_events_attr is None or not binding_events_attr.values[0]:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The BINDING_EVENTS attribute must be set to true.",
                ),
                loc=("attributes",),
                input=program.attributes,
                ctx={},
            )
        )

    return validation_errors or None
