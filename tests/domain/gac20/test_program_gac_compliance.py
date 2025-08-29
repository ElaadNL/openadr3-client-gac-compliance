import pytest
from openadr3_client.models.program.program import NewProgram
from pydantic import ValidationError


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
    with pytest.raises(ValidationError, match="The program must have bindingEvents set to True."):
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
    assert grouped_errors[0].get("type") == "value_error"
    assert grouped_errors[1].get("type") == "value_error"
    assert grouped_errors[0].get("msg") == "The program type must follow the format DSO_CPO_INTERFACE-x.x.x."
    assert grouped_errors[1].get("msg") == "The program must have bindingEvents set to True."
