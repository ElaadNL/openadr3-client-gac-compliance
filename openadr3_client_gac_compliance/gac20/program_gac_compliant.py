"""Module which implements GAC compliance validators for the program OpenADR3 types."""

import re

from openadr3_client.models.program.program import Program
from pydantic_core import InitErrorDetails, PydanticCustomError


def validate_program_gac_compliant(program: Program) -> list[InitErrorDetails] | None:
    """
    Validates that the program is GAC compliant.

    The following constraints are enforced for programs:
    - The program must have a retailer name
    - The retailer name must be between 2 and 128 characters long.
    - The program MUST have a programType.
    - The programType MUST equal "DSO_CPO_INTERFACE-x.x.x, where x.x.x is the version as defined in the GAC specification.
    - The program MUST have bindingEvents set to true.

    """  # noqa: E501
    validation_errors: list[InitErrorDetails] = []

    program_type_regex = (
        r"^DSO_CPO_INTERFACE-"
        r"(0|[1-9]\d*)\."
        r"(0|[1-9]\d*)\."
        r"(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))"
        r"?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
        r"$"
    )

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
                    "The program type must follow the format DSO_CPO_INTERFACE-x.x.x.",
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

    return validation_errors if validation_errors else None
