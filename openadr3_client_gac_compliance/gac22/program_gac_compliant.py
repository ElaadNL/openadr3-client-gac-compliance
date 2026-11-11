# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""Module which implements GAC 2.2 compliance validators for the program OpenADR3 types."""

from openadr3_client.oadr310.models.program.program import Program
from openadr3_client.oadr310.models.program.program_attribute import ProgramAttributeType
from pydantic_core import InitErrorDetails, PydanticCustomError

from openadr3_client_gac_compliance.gac22.identifiers import DSO_IDENTIFIERS


def validate_program_gac_compliant(program: Program) -> list[InitErrorDetails] | None:
    """
    Validates that the program is GAC compliant.

    The following constraints are enforced for programs (all in the `attributes` field):
    - The program must have a `RETAILER_NAME` attribute.
    - The `RETAILER_NAME` attribute must hold exactly one value, the EAN13 code of the issuing Dutch DSO.
    - The program MUST have a `PROGRAM_TYPE` attribute.
    - The `PROGRAM_TYPE` value MUST equal "DSO_CPO_INTERFACE-2.2.0".
    - The program MUST have a `BINDING_EVENTS` attribute set to exactly one value, the boolean true.

    """
    validation_errors: list[InitErrorDetails] = []

    program_type = "DSO_CPO_INTERFACE-2.2.0"

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
        retailer_names = retailer_name_attr.values
        has_single_value = len(retailer_names) == 1
        # isinstance guard: values are untyped JSON, and an unhashable one would crash the set lookup.
        is_dso_code = has_single_value and isinstance(retailer_names[0], str) and retailer_names[0] in DSO_IDENTIFIERS
        if not is_dso_code:
            validation_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "value_error",
                        "The RETAILER_NAME attribute must be the EAN13 code of a Dutch DSO.",
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
    elif program_type_attr.values != (program_type,):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.2.0.",
                ),
                loc=("attributes",),
                input=program.attributes,
                ctx={},
            )
        )

    binding_events_attr = attributes.get_by_type(ProgramAttributeType.BINDING_EVENTS) if attributes else None
    # `is True` guards against the library ever coercing other values (1, "true") to a truthy bool.
    if binding_events_attr is None or len(binding_events_attr.values) != 1 or binding_events_attr.values[0] is not True:
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
