# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Final

# The DSOs that may be addressed by a GAC 2.2 interface, identified by their EAN13.
DSO_IDENTIFIERS: Final[frozenset[str]] = frozenset(
    {
        "8716871000002",
        "8712423014022",
        "8716892000005",
        "8716916000004",
        "8716878999996",
        "8716912000008",
    }
)

# [0-9] rather than \d: \d also matches non-ASCII decimal digits, which are not part of an EAN.
_GRID_CONNECTION_IDENTIFIER = re.compile(r"EAN[0-9]{18}")


def is_grid_connection_identifier(value: object) -> bool:
    """Validates that the value is a grid connection identifier: 'EAN' followed by 18 ASCII digits."""
    return isinstance(value, str) and _GRID_CONNECTION_IDENTIFIER.fullmatch(value) is not None
