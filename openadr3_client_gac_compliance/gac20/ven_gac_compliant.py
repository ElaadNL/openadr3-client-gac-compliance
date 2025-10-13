import re

import pycountry
from openadr3_client.models.ven.ven import Ven
from pydantic_core import InitErrorDetails, PydanticCustomError


def validate_ven_gac_compliant(ven: Ven) -> list[InitErrorDetails] | None:
    """
    Validates that the VEN is GAC compliant.

    The following constraints are enforced for VENs:
    - The VEN must have a VEN name
    - The VEN name must be an eMI3 identifier.

    """
    validation_errors: list[InitErrorDetails] = []

    emi3_identifier_regex = r"^[A-Z]{2}-?[A-Z0-9]{3}$"

    if not re.fullmatch(emi3_identifier_regex, ven.ven_name):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The VEN name must be formatted as an eMI3 identifier.",
                ),
                loc=("ven_name",),
                input=ven.ven_name,
                ctx={},
            )
        )

    alpha_2_country = pycountry.countries.get(alpha_2=ven.ven_name[:2])

    if alpha_2_country is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The first two characters of the VEN name must be a valid ISO 3166-1 alpha-2 country code.",
                ),
                loc=("ven_name",),
                input=ven.ven_name,
                ctx={},
            )
        )

    return validation_errors if validation_errors else None
