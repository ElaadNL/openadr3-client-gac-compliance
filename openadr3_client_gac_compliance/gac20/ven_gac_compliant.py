import re
from openadr3_client.models.model import ValidatorRegistry, Model as ValidatorModel
from openadr3_client.models.ven.ven import Ven
import pycountry

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


@ValidatorRegistry.register(Ven, ValidatorModel())
def ven_gac_compliant(self: Ven) -> Ven:
    """Enforces that the ven is GAC compliant.

    GAC enforces the following constraints for vens:
    - The ven must have a ven name
    - The ven name must be an eMI3 identifier.
    """
    validation_errors: list[InitErrorDetails] = []

    emi3_identifier_regex = r"^[A-Z]{2}-?[A-Z0-9]{3}$"

    if not re.fullmatch(emi3_identifier_regex, self.ven_name):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The ven name must be formatted as an eMI3 identifier.",
                ),
                loc=("ven_name",),
                input=self.ven_name,
                ctx={},
            )
        )

    alpha_2_country = pycountry.countries.get(alpha_2=self.ven_name[:2])

    if alpha_2_country is None:
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The first two characters of the ven name must be a valid ISO 3166-1 alpha-2 country code.",
                ),
                loc=("ven_name",),
                input=self.ven_name,
                ctx={},
            )
        )

    if validation_errors:
        raise ValidationError.from_exception_data(
            title=self.__class__.__name__, line_errors=validation_errors
        )

    return self
