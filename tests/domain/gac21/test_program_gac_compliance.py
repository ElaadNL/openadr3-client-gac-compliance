# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re

import pytest
from openadr3_client._models.common.attribute import Attribute
from openadr3_client._models.common.value_map_collection import ValuesMap
from openadr3_client.oadr310.models.program.program import NewProgram
from openadr3_client.oadr310.models.program.program_attribute import ProgramAttributeType
from openadr3_client.plugin import ValidatorPluginRegistry
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac21.plugin import Gac21ValidatorPlugin

VALID_PROGRAM_TYPE = "DSO_CPO_INTERFACE-2.1.1"


def _create_program(
    retailer_name: str | None = "1234567890123",
    program_type: str | None = VALID_PROGRAM_TYPE,
    binding_events: bool | None = True,  # noqa: FBT001, FBT002
) -> NewProgram:
    """
    Helper function to create a program with the specified values.

    Args:
        retailer_name: The retailer name attribute value. None omits the attribute.
        program_type: The program type attribute value. None omits the attribute.
        binding_events: The bindingEvents attribute value. None omits the attribute.

    """
    attributes: list[Attribute] = []
    if retailer_name is not None:
        attributes.append(Attribute(type="RETAILER_NAME", values=(retailer_name,)))
    if program_type is not None:
        attributes.append(Attribute(type="PROGRAM_TYPE", values=(program_type,)))
    if binding_events is not None:
        attributes.append(Attribute(type="BINDING_EVENTS", values=(binding_events,)))

    return NewProgram(
        program_name="test-program",
        attributes=ValuesMap[ProgramAttributeType, Attribute](attributes) if attributes else None,
    )


@pytest.fixture(autouse=True)
def clear_plugins():
    """Clear plugins before each test and register GAC plugin."""
    ValidatorPluginRegistry.clear_plugins()
    ValidatorPluginRegistry.register_plugin(Gac21ValidatorPlugin.setup())
    yield
    ValidatorPluginRegistry.clear_plugins()


def test_program_gac_compliant_valid() -> None:
    """Test that a fully compliant program is accepted."""
    program = _create_program()

    assert program.program_name == "test-program"
    assert program.attributes is not None
    retailer_attr = next(a for a in program.attributes if a.type == "RETAILER_NAME")
    program_type_attr = next(a for a in program.attributes if a.type == "PROGRAM_TYPE")
    binding_events_attr = next(a for a in program.attributes if a.type == "BINDING_EVENTS")
    assert retailer_attr.values[0] == "1234567890123"
    assert program_type_attr.values[0] == VALID_PROGRAM_TYPE
    assert binding_events_attr.values[0] is True


def test_missing_retailer_name() -> None:
    """Test that a program without a retailer name attribute raises an error."""
    with pytest.raises(ValidationError, match=re.escape("The program must have a RETAILER_NAME attribute.")):
        _ = _create_program(retailer_name=None)


def test_retailer_name_too_short() -> None:
    """Test that a program with a retailer name that is too short raises an error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The RETAILER_NAME attribute must be between 2 and 128 characters long."),
    ):
        _ = _create_program(retailer_name="1")


def test_retailer_name_too_long() -> None:
    """Test that a program with a retailer name that is too long raises an error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The RETAILER_NAME attribute must be between 2 and 128 characters long."),
    ):
        _ = _create_program(retailer_name="1" * 129)


def test_missing_program_type() -> None:
    """Test that a program without a program type attribute raises an error."""
    with pytest.raises(ValidationError, match=re.escape("The program must have a PROGRAM_TYPE attribute.")):
        _ = _create_program(program_type=None)


def test_invalid_program_type_format() -> None:
    """Test that a program with an invalid program type raises an error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.1.1."),
    ):
        _ = _create_program(program_type="INVALID_FORMAT")


def test_invalid_program_type_version() -> None:
    """Test that a program with a different program type version raises an error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.1.1."),
    ):
        _ = _create_program(program_type="DSO_CPO_INTERFACE-1.0.0")


def test_binding_events_false() -> None:
    """Test that a program with bindingEvents set to False raises an error."""
    with pytest.raises(ValidationError, match=re.escape("The BINDING_EVENTS attribute must be set to true.")):
        _ = _create_program(binding_events=False)


def test_program_multiple_errors_grouped() -> None:
    """Test that multiple errors are grouped together and returned as a single error."""
    with pytest.raises(
        ValidationError,
        match=re.escape("2 validation errors for NewProgram"),
    ) as exc_info:
        _ = _create_program(program_type="DSO_CPO_INTERFACE-1.0.0", binding_events=False)

    grouped_errors = exc_info.value.errors()

    assert len(grouped_errors) == 2
    assert grouped_errors[0].get("type", None) == "value_error"
    assert grouped_errors[1].get("type", None) == "value_error"
    assert grouped_errors[0].get("msg", None) == "The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.1.1."
    assert grouped_errors[1].get("msg", None) == "The BINDING_EVENTS attribute must be set to true."


def test_plugin_system_integration() -> None:
    """Test that the plugin system correctly integrates with the Program validation."""
    validators = ValidatorPluginRegistry.get_model_validators(NewProgram)
    assert len(validators) == 1

    valid_program = _create_program()
    assert valid_program.program_name == "test-program"

    with pytest.raises(ValidationError) as exc_info:
        _create_program(retailer_name=None, program_type="INVALID", binding_events=False)

    errors = exc_info.value.errors()
    assert len(errors) == 3  # retailerName, programType, bindingEvents

    assert errors[0].get("msg", None) == "The program must have a RETAILER_NAME attribute."
    assert errors[1].get("msg", None) == "The PROGRAM_TYPE attribute must equal DSO_CPO_INTERFACE-2.1.1."
    assert errors[2].get("msg", None) == "The BINDING_EVENTS attribute must be set to true."


def test_plugin_error_details() -> None:
    """Test that plugin errors contain correct location and input information."""
    with pytest.raises(ValidationError) as exc_info:
        _create_program(retailer_name="X", program_type="BAD", binding_events=False)

    errors = exc_info.value.errors()
    assert len(errors) == 3

    assert errors[0].get("loc", None) == ("attributes",)
    assert errors[1].get("loc", None) == ("attributes",)
    assert errors[2].get("loc", None) == ("attributes",)


def test_plugin_with_edge_cases() -> None:
    """Test plugin validation with various edge cases."""
    test_cases = [
        (None, None, False, 3),  # All three validations fail
        ("Valid", None, False, 2),  # programType and bindingEvents fail
        (None, VALID_PROGRAM_TYPE, False, 2),  # retailerName and bindingEvents fail
        (None, "DSO_CPO_INTERFACE-1.0.0", False, 3),  # retailerName, programType, bindingEvents fail
        ("X", VALID_PROGRAM_TYPE, True, 1),  # Only retailerName too short
        ("X", "DSO_CPO_INTERFACE-1.0.0", True, 2),  # retailerName too short and wrong programType
        ("Valid", "INVALID", True, 1),  # Only programType invalid
        ("Valid", "DSO_CPO_INTERFACE-1.0.0", False, 2),  # programType invalid and bindingEvents false
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
