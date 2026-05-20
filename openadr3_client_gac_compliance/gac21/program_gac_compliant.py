# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""Module which implements GAC 2.1 compliance validators for the program OpenADR3 types."""

import re

from openadr3_client.oadr310.models.program.program import Program
from pydantic_core import InitErrorDetails, PydanticCustomError


def validate_program_gac_compliant(program: Program) -> list[InitErrorDetails] | None:
    """
    Validates that the program is GAC compliant.

    The following constraints are enforced for programs:
    - The program must have a retailer name
    - The retailer name must be between 2 and 128 characters long.
    - The program MUST have a programType.
    - The programType MUST equal "DSO_CPO_INTERFACE-2.1.0".
    - The program MUST have bindingEvents set to true.

    """
    validation_errors: list[InitErrorDetails] = []

    program_type_regex = r"^DSO_CPO_INTERFACE-2\.1\.0$"

    if program.retailer_name is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a retailer name.",
                ),
                loc=("retailer_name",),
                input=program.retailer_name,
                ctx={},
            )
        )

    if program.retailer_name is not None and (
        len(program.retailer_name) < 2 or len(program.retailer_name) > 128  # noqa: PLR2004
    ):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The retailer name must be between 2 and 128 characters long.",
                ),
                loc=("retailer_name",),
                input=program.retailer_name,
                ctx={},
            )
        )

    if program.program_type is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a program type.",
                ),
                loc=("program_type",),
                input=program.program_type,
                ctx={},
            )
        )
    if program.program_type is not None and not re.fullmatch(program_type_regex, program.program_type):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program type must equal DSO_CPO_INTERFACE-2.1.0.",
                ),
                loc=("program_type",),
                input=program.program_type,
                ctx={},
            )
        )

    if program.binding_events is False:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have bindingEvents set to true.",
                ),
                loc=("binding_events",),
                input=program.binding_events,
                ctx={},
            )
        )

    return validation_errors or None
