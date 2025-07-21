import pytest

from pydantic import ValidationError
from openadr3_client.models.ven.ven import NewVen


def _create_ven(ven_name: str) -> NewVen:
    """Helper function to create a ven with the specified values.

    Args:
        ven_name: The ven name of the ven.
    """
    return NewVen(ven_name=ven_name)


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


def test_ven_multiple_errors_grouped() -> None:
    """Test that multiple errors are grouped together and returned as a single error."""
    with pytest.raises(
        ValidationError,
        match="2 validation errors for NewVen",
    ) as exc_info:
        _ = _create_ven("ZZ-123455667")

    grouped_errors = exc_info.value.errors()

    assert len(grouped_errors) == 2
    assert grouped_errors[0].get("type") == "value_error"
    assert grouped_errors[1].get("type") == "value_error"
    assert (
        grouped_errors[0].get("msg")
        == "The ven name must be formatted as an eMI3 identifier."
    )
    assert (
        grouped_errors[1].get("msg")
        == "The first two characters of the ven name must be a valid ISO 3166-1 alpha-2 country code."
    )
