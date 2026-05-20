# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re

import pycountry
from openadr3_client.oadr310.models.ven.ven import NewVenBlRequest, ServerVen, Ven
from pydantic_core import InitErrorDetails, PydanticCustomError

EAN18_REGEX = r"^\d{18}$"


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

    validation_errors.extend(_targets_compliant(ven))
    return validation_errors or None
