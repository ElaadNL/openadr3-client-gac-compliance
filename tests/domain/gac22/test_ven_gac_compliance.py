# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime

import pytest
from openadr3_client.oadr310.models.ven.ven import ExistingVen, NewVenVenRequest
from pydantic import ValidationError

VALID_TARGET = "EAN876543211234567890"
VALID_VEN_NAME = "8712345678906"


def _create_existing_ven(
    ven_name: str = VALID_VEN_NAME,
    targets: tuple[str, ...] | None = (VALID_TARGET,),
) -> ExistingVen:
    """Create a VEN as the VTN returns it, which is the form that carries targets."""
    now = datetime.now(tz=UTC)
    return ExistingVen(
        id="test-ven",
        ven_name=ven_name,
        created_date_time=now,
        modification_date_time=now,
        clientID="test-client",
        targets=targets,
    )


def test_ven_valid() -> None:
    """A VEN with an EAN13 name and EAN-prefixed targets is accepted."""
    ven = _create_existing_ven()

    assert ven.targets == (VALID_TARGET,)


@pytest.mark.parametrize(
    "targets",
    [
        ("876543211234567890",),
        ("EAN" + "\N{ARABIC-INDIC DIGIT ONE}" * 18,),
        ("EAN87654321123456789",),
        ("ean876543211234567890",),
        (" EAN876543211234567890",),
        (),
        None,
    ],
    ids=["bare-digits", "arabic-indic", "ean-plus-17", "lowercase", "leading-space", "empty", "missing"],
)
def test_ven_targets_invalid(targets: tuple[str, ...] | None) -> None:
    """Targets must be a non-empty list of EAN-prefixed grid connection identifiers."""
    with pytest.raises(ValidationError, match="grid connection identifiers"):
        _create_existing_ven(targets=targets)


def test_ven_ven_request_without_targets_passes() -> None:
    """A VEN client request cannot carry targets, so their absence is not an error."""
    ven = NewVenVenRequest(ven_name=VALID_VEN_NAME)

    assert ven.ven_name == VALID_VEN_NAME


def test_ven_name_invalid_check_digit() -> None:
    """The VEN name must be an EAN13 with a valid check digit."""
    with pytest.raises(ValidationError, match="EAN13"):
        _create_existing_ven(ven_name="8712345678901")
