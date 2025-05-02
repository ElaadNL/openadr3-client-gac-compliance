"""Module which implements GAC compliance validators for the program OpenADR3 types."""

from openadr3_client.models.program.program import Program
from openadr3_client.models.model import ValidatorRegistry, Model as ValidatorModel

import re


@ValidatorRegistry.register(Program, ValidatorModel())
def program_gac_compliant(self: Program) -> Program:
    """Enforces that the program is GAC compliant.

    GAC enforces the following constraints for programs:
    - The program must have a retailer name
    - The retailer name must be an EAN13 identifier.
    - The program MUST have a programType.
    - The programType MUST equal "DSO_CPO_INTERFACE-x.x.x, where x.x.x is the version as defined in the GAC specification.
    - The program MUST have bindingEvents set to True.
    are allowed there.
    """
    program_type_regex = r"^DSO_CPO_INTERFACE-(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    if self.retailer_name is None:
        raise ValueError("The program must have a retailer name.")
    if not re.fullmatch(r"\d{13}", self.retailer_name):
        raise ValueError("The retailer name must be an EAN13 identifier.")

    if self.program_type is None:
        raise ValueError("The program must have a program type.")
    if not re.fullmatch(program_type_regex, self.program_type):
        raise ValueError(
            "The program type must follow the format DSO_CPO_INTERFACE-x.x.x."
        )

    if self.binding_events is False:
        raise ValueError("The program must have bindingEvents set to True.")

    return self
