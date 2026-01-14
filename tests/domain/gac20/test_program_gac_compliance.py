# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from openadr3_client.models.program.program import NewProgram
from openadr3_client.plugin import ValidatorPluginRegistry
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac20.plugin import Gac20ValidatorPlugin


def _create_program(
    retailer_name: str | None = "1234567890123",
    program_type: str | None = "DSO_CPO_INTERFACE-1.0.0",
    binding_events: bool = True,  # noqa: FBT001, FBT002
) -> NewProgram:
    """
    Helper function to create a program with the specified values.

    Args:
        retailer_name: The retailer name of the program.
        program_type: The program type of the program.
        binding_events: Whether the program has binding events.

    """
    return NewProgram(
        program_name="test-program",
        retailer_name=retailer_name,
        program_type=program_type,
        binding_events=binding_events,
    )


@pytest.fixture(autouse=True)
def clear_plugins():
    """Clear plugins before each test and register GAC plugin."""
    ValidatorPluginRegistry.clear_plugins()
    ValidatorPluginRegistry.register_plugin(Gac20ValidatorPlugin.setup())
    yield
    ValidatorPluginRegistry.clear_plugins()


def test_program_gac_compliant_valid() -> None:
    """Test that a fully compliant program is accepted."""
    program = _create_program()

    assert program.program_name == "test-program"
    assert program.retailer_name == "1234567890123"
    assert program.program_type == "DSO_CPO_INTERFACE-1.0.0"
    assert program.binding_events is True


def test_missing_retailer_name() -> None:
    """Test that a program without a retailer name raises an error."""
    with pytest.raises(ValidationError, match="The program must have a retailer name."):
        _ = _create_program(retailer_name=None)


def test_retailer_name_too_short() -> None:
    """Test that a program with a retailer name that is too short raises an error."""
    with pytest.raises(
        ValidationError,
        match="The retailer name must be between 2 and 128 characters long.",
    ):
        _ = _create_program(retailer_name="1")


def test_retailer_name_too_long() -> None:
    """Test that a program with a retailer name that is too long raises an error."""
    with pytest.raises(
        ValidationError,
        match="The retailer name must be between 2 and 128 characters long.",
    ):
        _ = _create_program(retailer_name="1" * 129)


def test_missing_program_type() -> None:
    """Test that a program without a program type raises an error."""
    with pytest.raises(ValidationError, match="The program must have a program type."):
        _ = _create_program(program_type=None)


def test_invalid_program_type_format() -> None:
    """Test that a program with an invalid program type format raises an error."""
    with pytest.raises(
        ValidationError,
        match="The program type must follow the format DSO_CPO_INTERFACE-x.x.x.",
    ):
        _ = _create_program(program_type="INVALID_FORMAT")


def test_invalid_program_type_version() -> None:
    """Test that a program with an invalid program type version raises an error."""
    with pytest.raises(
        ValidationError,
        match="The program type must follow the format DSO_CPO_INTERFACE-x.x.x.",
    ):
        _ = _create_program(program_type="DSO_CPO_INTERFACE-invalid")


def test_binding_events_false() -> None:
    """Test that a program with binding_events set to False raises an error."""
    with pytest.raises(ValidationError, match="The program must have bindingEvents set to true."):
        _ = _create_program(binding_events=False)


def test_program_multiple_errors_grouped() -> None:
    """Test that multiple errors are grouped together and returned as a single error."""
    with pytest.raises(
        ValidationError,
        match="2 validation errors for NewProgram",
    ) as exc_info:
        _ = _create_program(program_type="DSO_CPO_INTERFACE-invalid", binding_events=False)

    grouped_errors = exc_info.value.errors()

    assert len(grouped_errors) == 2
    assert grouped_errors[0].get("type", None) == "value_error"
    assert grouped_errors[1].get("type", None) == "value_error"
    assert grouped_errors[0].get("msg", None) == "The program type must follow the format DSO_CPO_INTERFACE-x.x.x."
    assert grouped_errors[1].get("msg", None) == "The program must have bindingEvents set to true."


def test_plugin_system_integration() -> None:
    """Test that the plugin system correctly integrates with the Program validation."""
    validators = ValidatorPluginRegistry.get_model_validators(NewProgram)
    assert len(validators) == 1

    valid_program = _create_program()
    assert valid_program.program_name == "test-program"

    with pytest.raises(ValidationError) as exc_info:
        _create_program(retailer_name=None, program_type="INVALID", binding_events=False)

    errors = exc_info.value.errors()
    assert len(errors) == 3  # retailer_name, program_type, binding_events

    assert errors[0].get("msg", None) == "The program must have a retailer name."
    assert errors[1].get("msg", None) == "The program type must follow the format DSO_CPO_INTERFACE-x.x.x."
    assert errors[2].get("msg", None) == "The program must have bindingEvents set to true."


def test_plugin_error_details() -> None:
    """Test that plugin errors contain correct location and input information."""
    with pytest.raises(ValidationError) as exc_info:
        _create_program(retailer_name="X", program_type="BAD", binding_events=False)

    errors = exc_info.value.errors()
    assert len(errors) == 3

    assert errors[0].get("loc", None) == ("retailer_name",)
    assert errors[1].get("loc", None) == ("program_type",)
    assert errors[2].get("loc", None) == ("binding_events",)


def test_plugin_with_edge_cases() -> None:
    """Test plugin validation with various edge cases."""
    test_cases = [
        (None, None, False, 3),  # All three validations fail
        ("Valid", None, False, 2),  # program_type and binding_events fail
        (None, "DSO_CPO_INTERFACE-1.0.0", False, 2),  # retailer_name and binding_events fail
        ("X", "DSO_CPO_INTERFACE-1.0.0", True, 1),  # Only retailer_name too short
        ("Valid", "INVALID", True, 1),  # Only program_type invalid
        ("Valid", "DSO_CPO_INTERFACE-1.0.0", False, 1),  # Only binding_events false
    ]

    for retailer_name, program_type, binding_events, expected_error_count in test_cases:
        with pytest.raises(ValidationError) as exc_info:
            _create_program(retailer_name=retailer_name, program_type=program_type, binding_events=binding_events)

        errors = exc_info.value.errors()
        assert len(errors) == expected_error_count, (
            f"Expected {expected_error_count} errors for "
            f"retailer_name='{retailer_name}', program_type='{program_type}', "
            f"binding_events={binding_events}, got {len(errors)}"
        )
