# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re
from datetime import UTC, datetime

import pytest
from openadr3_client.oadr310.models.ven.ven import (
    ExistingVen,
    NewVen,
    NewVenBlRequest,
    VenUpdateBlRequest,
    VenUpdateVenRequest,
)
from openadr3_client.plugin import ValidatorPluginRegistry
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac21.plugin import Gac21ValidatorPlugin

VALID_EAN18 = "123456789012345678"


def _create_ven(ven_name: str) -> NewVen:
    """
    Helper function to create a VEN with the specified values.

    Args:
        ven_name: The name of the VEN.

    """
    return NewVen(ven_name=ven_name)


def _create_bl_ven(
    ven_name: str = "NL-ABC",
    targets: tuple[str, ...] | None = (VALID_EAN18,),
) -> NewVenBlRequest:
    """
    Helper function to create a BL VEN request with the specified values.

    Args:
        ven_name: The name of the VEN.
        targets: The targets of the VEN.

    """
    return NewVenBlRequest(
        ven_name=ven_name,
        clientID="test-client",
        targets=targets,
    )


def _create_bl_ven_update(
    ven_name: str = "NL-ABC",
    targets: tuple[str, ...] | None = (VALID_EAN18,),
) -> VenUpdateBlRequest:
    """
    Helper function to create a BL VEN update request with the specified values.

    Args:
        ven_name: The name of the VEN.
        targets: The targets of the VEN.

    """
    return VenUpdateBlRequest(
        ven_name=ven_name,
        clientID="test-client",
        targets=targets,
    )


def _create_ven_update(ven_name: str = "NL-ABC") -> VenUpdateVenRequest:
    """
    Helper function to create a VEN update request with the specified values.

    Args:
        ven_name: The name of the VEN.

    """
    return VenUpdateVenRequest(ven_name=ven_name)


def _create_existing_ven(
    ven_name: str = "NL-ABC",
    targets: tuple[str, ...] | None = (VALID_EAN18,),
) -> ExistingVen:
    """
    Helper function to create an existing VEN with the specified values.

    Args:
        ven_name: The name of the VEN.
        targets: The targets of the VEN.

    """
    now = datetime.now(tz=UTC)
    return ExistingVen(
        id="test-ven",
        ven_name=ven_name,
        created_date_time=now,
        modification_date_time=now,
        clientID="test-client",
        targets=targets,
    )


@pytest.fixture(autouse=True)
def clear_plugins():
    """Clear plugins before each test and register GAC plugin."""
    ValidatorPluginRegistry.clear_plugins()
    ValidatorPluginRegistry.register_plugin(Gac21ValidatorPlugin.setup())
    yield
    ValidatorPluginRegistry.clear_plugins()


def test_ven_gac_compliant_valid() -> None:
    """Test that a VEN with an eMI3 identifier as VEN name is accepted."""
    _ = _create_ven("NL-ABC")


def test_ven_gac_compliant_invalid_format() -> None:
    """Test that a VEN with a VEN name that does not follow the eMI3 identifier format is rejected."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The VEN name must be formatted as an eMI3 identifier."),
    ):
        _ = _create_ven("ABCDEFG")


def test_ven_gac_compliant_invalid_country_code() -> None:
    """Test that a VEN with a VEN name that does not have a valid ISO 3166-1 alpha-2 country code is rejected."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The first two characters of the VEN name must be a valid ISO 3166-1 alpha-2 country code."),
    ):
        _ = _create_ven("ZZ-123")


def test_ven_multiple_errors_grouped() -> None:
    """Test that multiple errors are grouped together and returned as a single error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("2 validation errors for NewVen"),
    ) as exc_info:
        _ = _create_ven("ZZ-123455667")

    grouped_errors = exc_info.value.errors()

    assert len(grouped_errors) == 2
    assert grouped_errors[0].get("type", None) == "value_error"
    assert grouped_errors[1].get("type", None) == "value_error"
    assert grouped_errors[0].get("msg", None) == "The VEN name must be formatted as an eMI3 identifier."
    assert (
        grouped_errors[1].get("msg", None)
        == "The first two characters of the VEN name must be a valid ISO 3166-1 alpha-2 country code."
    )


def test_ven_targets_compliant_valid() -> None:
    """Test that a BL VEN request with valid EAN18 targets is accepted."""
    ven = _create_bl_ven(targets=(VALID_EAN18, "987654321098765432"))

    assert ven.targets == (VALID_EAN18, "987654321098765432")


def test_ven_targets_empty_valid() -> None:
    """Test that a BL VEN request without targets is accepted."""
    ven = _create_bl_ven(targets=None)

    assert ven.targets is None


def test_ven_targets_invalid_format() -> None:
    """Test that a BL VEN request with invalid targets is rejected."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The targets value must be a list of 'EAN18' values."),
    ):
        _ = _create_bl_ven(targets=("not-an-ean18",))


def test_ven_update_targets_compliant_valid() -> None:
    """Test that a BL VEN update request with valid EAN18 targets is accepted."""
    ven = _create_bl_ven_update(targets=(VALID_EAN18, "987654321098765432"))

    assert ven.targets == (VALID_EAN18, "987654321098765432")


def test_ven_update_targets_empty_valid() -> None:
    """Test that a BL VEN update request without targets is accepted."""
    ven = _create_bl_ven_update(targets=None)

    assert ven.targets is None


def test_ven_update_targets_invalid_format() -> None:
    """Test that a BL VEN update request with invalid targets is rejected."""
    existing_ven = _create_existing_ven()

    with pytest.raises(
        ValidationError,
        match=re.escape("The targets value must be a list of 'EAN18' values."),
    ):
        existing_ven.update(_create_bl_ven_update(targets=("not-an-ean18",)))


def test_ven_update_ven_request_without_targets_valid() -> None:
    """Test that a VEN update request without a targets field is accepted."""
    ven = _create_ven_update()

    assert ven.ven_name == "NL-ABC"


def test_plugin_system_integration() -> None:
    """Test that the plugin system correctly integrates with the VEN validation."""
    validators = ValidatorPluginRegistry.get_model_validators(NewVen)
    assert len(validators) == 1

    valid_ven = _create_ven("NL-ABC")
    assert valid_ven.ven_name == "NL-ABC"

    with pytest.raises(ValidationError) as exc_info:
        _create_ven("INVALID")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0].get("msg", None) == "The VEN name must be formatted as an eMI3 identifier."


def test_plugin_error_details() -> None:
    """Test that plugin errors contain correct location and input information."""
    with pytest.raises(ValidationError) as exc_info:
        _create_ven("XX-TOOLONG")

    errors = exc_info.value.errors()
    assert len(errors) == 2

    assert errors[0].get("loc", None) == ("ven_name",)
    assert errors[0].get("input", None) == "XX-TOOLONG"
    assert errors[0].get("type", None) == "value_error"
    assert errors[1].get("loc", None) == ("ven_name",)
    assert errors[1].get("input", None) == "XX-TOOLONG"
    assert errors[1].get("type", None) == "value_error"


def test_plugin_with_edge_cases() -> None:
    """Test plugin validation with various edge cases."""
    test_cases = [
        ("ZZ-123455667", 2),  # Invalid country code and format - both GAC validations fail
        ("NL-TOOLONG", 1),  # Valid country, invalid format - only format fails
        ("XX-ABC", 1),  # Invalid country, valid format - only country fails
        ("ZZ-123", 1),  # Invalid country, valid format - only country fails
    ]

    for ven_name, expected_error_count in test_cases:
        with pytest.raises(ValidationError) as exc_info:
            _create_ven(ven_name)

        errors = exc_info.value.errors()
        assert len(errors) == expected_error_count, (
            f"Expected {expected_error_count} errors for '{ven_name}', got {len(errors)}"
        )
