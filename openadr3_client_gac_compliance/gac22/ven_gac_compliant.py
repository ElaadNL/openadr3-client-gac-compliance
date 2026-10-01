# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re

from openadr3_client.oadr310.models.ven.ven import NewVenBlRequest, ServerVen, Ven
from pydantic_core import InitErrorDetails, PydanticCustomError

EAN18_REGEX = r"^\d{18}$"
EAN13_LENGTH = 13


def _has_valid_check_digit(value: str) -> bool:
    """
    Validates the trailing check digit of an EAN.

    One routine covers both lengths. Reading right to left from the digit before the check digit,
    digits are weighted 3, 1, 3, 1 and summed; the check digit is that sum's complement to the next
    multiple of ten.
    """
    digits = [int(digit) for digit in value]
    *body, check_digit = digits
    weighted = sum(digit * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(body)))
    return (10 - weighted % 10) % 10 == check_digit


def _is_ean(value: object, length: int) -> bool:
    """Validates that the value is an EAN of the given length, with a valid check digit."""
    return (
        isinstance(value, str)
        and len(value) == length
        # str.isdigit accepts unicode decimal digits, which are not an EAN.
        and value.isascii()
        and value.isdigit()
        and _has_valid_check_digit(value)
    )


def is_ean13(value: object) -> bool:
    """Validates that the value is the EAN13 code of a market party, such as a DSO or a Service Provider."""
    return _is_ean(value, EAN13_LENGTH)


def _get_ven_targets(ven: Ven) -> tuple[str, ...]:
    """Return the targets of the VEN if they are present on the model."""
    if not isinstance(ven, ServerVen | NewVenBlRequest):
        return ()

    return ven.targets or ()


def _targets_compliant(ven: Ven) -> list[InitErrorDetails]:
    """
    Validates that the targets of the VEN are GAC compliant.

    The following constraints are enforced for targets:

    - The targets value must be a list of 'EAN18' values.
    """
    validation_errors: list[InitErrorDetails] = []

    targets = _get_ven_targets(ven)

    if not all(re.fullmatch(EAN18_REGEX, target) for target in targets):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The targets value must be a list of 'EAN18' values.",
                ),
                loc=("targets",),
                input=targets,
                ctx={},
            )
        )

    return validation_errors


def validate_ven_gac_compliant(ven: Ven) -> list[InitErrorDetails] | None:
    """
    Validates that the VEN is GAC 2.1 compliant.

    The following constraints are enforced for VENs:
    - The VEN must have a VEN name
    - The VEN name must be an eMI3 identifier.
    - When present, the targets must be a list of 'EAN18' values.

    """
    validation_errors: list[InitErrorDetails] = []

    if not is_ean13(ven.ven_name):
        validation_errors.append(
            InitErrorDetails(
                type=PydanticCustomError(
                    "value_error",
                    "The VEN name must be an EAN13 of 13 digits with a valid check digit.",
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

    validation_errors.extend(_targets_compliant(ven))
    return validation_errors or None
