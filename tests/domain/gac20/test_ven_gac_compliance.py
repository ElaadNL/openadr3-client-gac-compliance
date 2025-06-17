import pytest

from pydantic import ValidationError
from openadr3_client.models.ven.ven import NewVen


def _create_ven(ven_name: str) -> NewVen:
    """Helper function to create a ven with the specified values.

    Args:
        ven_name: The ven name of the ven.
    """
    return NewVen(id=None, ven_name=ven_name)


def test_ven_gac_compliant_valid() -> None:
    """Test that a ven with an eMI3 identifier as ven name is accepted."""
    _ = _create_ven("NL-ABC")


def test_ven_gac_compliant_invalid_format() -> None:
    """Test that a ven with a ven name that does not follow the eMI3 identifier format is rejected."""
    with pytest.raises(
        ValidationError,
        match="The ven name must be formatted as an eMI3 identifier.",
    ):
        _ = _create_ven("ABCDEFG")


def test_ven_gac_compliant_invalid_country_code() -> None:
    """Test that a ven with a ven name that does not have a valid ISO 3166-1 alpha-2 country code is rejected."""
    with pytest.raises(
        ValidationError,
        match="The first two characters of the ven name must be a valid ISO 3166-1 alpha-2 country code.",
    ):
        _ = _create_ven("ZZ-123")
