import pytest

from pydantic import ValidationError
from openadr3_client.models.program.program import NewProgram


def _create_program(
    retailer_name: str | None = "1234567890123",
    program_type: str | None = "DSO_CPO_INTERFACE-1.0.0",
    binding_events: bool = True,
) -> NewProgram:
    """Helper function to create a program with the specified values.

    Args:
        retailer_name: The retailer name of the program.
        program_type: The program type of the program.
        binding_events: Whether the program has binding events.
    """
    return NewProgram(
        id=None,
        program_name="test-program",
        retailer_name=retailer_name,
        program_type=program_type,
        binding_events=binding_events,
    )


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


def test_invalid_retailer_name_format() -> None:
    """Test that a program with an invalid retailer name format raises an error."""
    with pytest.raises(
        ValidationError, match="The retailer name must be an EAN13 identifier."
    ):
        _ = _create_program(retailer_name="invalid-ean")


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
    with pytest.raises(
        ValidationError, match="The program must have bindingEvents set to True."
    ):
        _ = _create_program(binding_events=False)
