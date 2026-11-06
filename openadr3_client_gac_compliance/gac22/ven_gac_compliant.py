# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from openadr3_client.oadr310.models.ven.ven import NewVenBlRequest, ServerVen, Ven
from pydantic_core import InitErrorDetails, PydanticCustomError

from openadr3_client_gac_compliance.gac22.identifiers import is_grid_connection_identifier

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


def _targets_compliant(ven: Ven) -> list[InitErrorDetails]:
    """
    Validates that the targets of the VEN are GAC compliant.

    Only VENs that can carry targets are checked: a VEN client request has no targets field, because
    targets are assigned by a BL client. For the others, the targets must be a non-empty list of grid
    connection identifiers.
    """
    if not isinstance(ven, ServerVen | NewVenBlRequest):
        return []

    targets = ven.targets
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


def validate_ven_gac_compliant(ven: Ven) -> list[InitErrorDetails] | None:
    """
    Validates that the VEN is GAC 2.2 compliant.

    The following constraints are enforced for VENs:
    - The VEN name must be an EAN13 with a valid check digit.
    - A VEN that can carry targets must have a non-empty list of grid connection identifiers.
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

    validation_errors.extend(_targets_compliant(ven))
    return validation_errors or None
