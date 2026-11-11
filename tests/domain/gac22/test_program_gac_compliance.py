# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any

import pytest
from openadr3_client._models.common.attribute import Attribute
from openadr3_client._models.common.value_map_collection import ValuesMap
from openadr3_client.oadr310.models.program.program import NewProgram
from openadr3_client.oadr310.models.program.program_attribute import ProgramAttributeType
from pydantic import ValidationError

from openadr3_client_gac_compliance.gac22.identifiers import DSO_IDENTIFIERS

VALID_RETAILER_NAME = "8716871000002"
VALID_PROGRAM_TYPE = "DSO_CPO_INTERFACE-2.2.0"


def _create_program(
    retailer_name: tuple[Any, ...] | None = (VALID_RETAILER_NAME,),
    program_type: tuple[Any, ...] | None = (VALID_PROGRAM_TYPE,),
    binding_events: tuple[Any, ...] | None = (True,),
) -> NewProgram:
    """
    Create a program with the given attribute values.

    Args:
        retailer_name: The RETAILER_NAME values. None omits the attribute.
        program_type: The PROGRAM_TYPE values. None omits the attribute.
        binding_events: The BINDING_EVENTS values. None omits the attribute.

    """
    attributes: list[Attribute] = []
    if retailer_name is not None:
        attributes.append(Attribute(type="RETAILER_NAME", values=retailer_name))
    if program_type is not None:
        attributes.append(Attribute(type="PROGRAM_TYPE", values=program_type))
    if binding_events is not None:
        attributes.append(Attribute(type="BINDING_EVENTS", values=binding_events))

    return NewProgram(
        program_name="test-program",
        attributes=ValuesMap[ProgramAttributeType, Attribute](attributes) if attributes else None,
    )


@pytest.mark.parametrize("code", sorted(DSO_IDENTIFIERS))
def test_retailer_name_each_dso_code_passes(code: str) -> None:
    """Every DSO EAN13 code from the spec is accepted as RETAILER_NAME."""
    program = _create_program(retailer_name=(code,))

    assert program.attributes is not None


@pytest.mark.parametrize(
    "values",
    [
        ("LIANDER",),
        ("8716871000002", "LIANDER"),
        (),
        ({"a": 1},),
        ([1],),
        ("8716871000002", "8712423014022"),
    ],
    ids=["unknown-code", "valid-plus-unknown", "empty", "dict", "list", "two-valid-codes"],
)
def test_retailer_name_invalid(values: tuple[Any, ...]) -> None:
    """RETAILER_NAME must be exactly one string, and that string a DSO EAN13 code; unhashable values must not crash."""
    with pytest.raises(ValidationError, match=re.escape("EAN13 code of a Dutch DSO")):
        _ = _create_program(retailer_name=values)


def test_missing_retailer_name() -> None:
    """A program without RETAILER_NAME is rejected."""
    with pytest.raises(ValidationError, match=re.escape("The program must have a RETAILER_NAME attribute.")):
        _ = _create_program(retailer_name=None)


def test_program_type_220_passes() -> None:
    """PROGRAM_TYPE DSO_CPO_INTERFACE-2.2.0 is accepted."""
    program = _create_program(program_type=("DSO_CPO_INTERFACE-2.2.0",))

    assert program.attributes is not None


def test_program_type_211_fails() -> None:
    """The previous spec version is rejected."""
    with pytest.raises(ValidationError, match=re.escape("DSO_CPO_INTERFACE-2.2.0")):
        _ = _create_program(program_type=("DSO_CPO_INTERFACE-2.1.1",))


def test_program_type_multiple_values_fails() -> None:
    """PROGRAM_TYPE must be exactly the 2.2.0 value; an extra value next to it is rejected."""
    with pytest.raises(ValidationError, match=re.escape("DSO_CPO_INTERFACE-2.2.0")):
        _ = _create_program(program_type=("DSO_CPO_INTERFACE-2.2.0", "other"))


def test_missing_program_type() -> None:
    """A program without PROGRAM_TYPE is rejected."""
    with pytest.raises(ValidationError, match=re.escape("The program must have a PROGRAM_TYPE attribute.")):
        _ = _create_program(program_type=None)


@pytest.mark.parametrize("values", [("true",), (1,)])
def test_binding_events_non_boolean_rejected(values: tuple[Any, ...]) -> None:
    """Non-boolean BINDING_EVENTS values are rejected, whether by the client library or by the validator."""
    with pytest.raises(ValidationError):
        _ = _create_program(binding_events=values)


@pytest.mark.parametrize("values", [(False,), ()])
def test_binding_events_not_true(values: tuple[Any, ...]) -> None:
    """BINDING_EVENTS must be exactly one literal true; empty values must not raise IndexError."""
    with pytest.raises(ValidationError, match=re.escape("The BINDING_EVENTS attribute must be set to true.")):
        _ = _create_program(binding_events=values)


def test_missing_binding_events() -> None:
    """A program without BINDING_EVENTS is rejected."""
    with pytest.raises(ValidationError, match=re.escape("The BINDING_EVENTS attribute must be set to true.")):
        _ = _create_program(binding_events=None)


def test_should_fields_absent_and_payload_descriptors_present_pass() -> None:
    """SHOULD-level fields (RETAILER_LONG_NAME, COUNTRY) and payload descriptors do not cause rejection."""
    program = NewProgram(
        program_name="test-program",
        attributes=ValuesMap[ProgramAttributeType, Attribute](
            [
                Attribute(type="RETAILER_NAME", values=(VALID_RETAILER_NAME,)),
                Attribute(type="PROGRAM_TYPE", values=(VALID_PROGRAM_TYPE,)),
                Attribute(type="BINDING_EVENTS", values=(True,)),
            ]
        ),
        payload_descriptors=(),
    )

    assert program.attributes is not None
