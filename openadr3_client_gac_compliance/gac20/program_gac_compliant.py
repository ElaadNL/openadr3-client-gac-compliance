"""Module which implements GAC compliance validators for the program OpenADR3 types."""

from openadr3_client.models.program.program import Program
from openadr3_client.models.model import ValidatorRegistry, Model as ValidatorModel

import re

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


@ValidatorRegistry.register(Program, ValidatorModel())
def program_gac_compliant(self: Program) -> Program:
    """Enforces that the program is GAC compliant.

    GAC enforces the following constraints for programs:
    - The program must have a retailer name
    - The retailer name must be between 2 and 128 characters long.
    - The program MUST have a programType.
    - The programType MUST equal "DSO_CPO_INTERFACE-x.x.x, where x.x.x is the version as defined in the GAC specification.
    - The program MUST have bindingEvents set to True.
    are allowed there.
    """
    validation_errors: list[InitErrorDetails] = []

    program_type_regex = r"^DSO_CPO_INTERFACE-(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    if self.retailer_name is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a retailer name.",
                ),
                loc=("retailer_name",),
                input=self.retailer_name,
                ctx={},
            )
        )

    if self.retailer_name is not None and (
        len(self.retailer_name) < 2 or len(self.retailer_name) > 128
    ):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The retailer name must be between 2 and 128 characters long.",
                ),
                loc=("retailer_name",),
                input=self.retailer_name,
                ctx={},
            )
        )

    if self.program_type is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have a program type.",
                ),
                loc=("program_type",),
                input=self.program_type,
                ctx={},
            )
        )
    if self.program_type is not None and not re.fullmatch(
        program_type_regex, self.program_type
    ):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program type must follow the format DSO_CPO_INTERFACE-x.x.x.",
                ),
                loc=("program_type",),
                input=self.program_type,
                ctx={},
            )
        )

    if self.binding_events is False:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The program must have bindingEvents set to True.",
                ),
                loc=("binding_events",),
                input=self.binding_events,
                ctx={},
            )
        )

    if validation_errors:
        raise ValidationError.from_exception_data(
            title=self.__class__.__name__, line_errors=validation_errors
        )

    return self
