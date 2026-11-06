<!--
SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>

SPDX-License-Identifier: Apache-2.0
-->

[![CodeQL Advanced](https://github.com/ElaadNL/openadr3-client-gac-compliance/actions/workflows/codeql.yml/badge.svg)](https://github.com/ElaadNL/openadr3-client-gac-compliance/actions/workflows/codeql.yml)
[![Python Default CI](https://github.com/ElaadNL/openadr3-client-gac-compliance/actions/workflows/ci.yml/badge.svg)](https://github.com/ElaadNL/openadr3-client-gac-compliance/actions/workflows/ci.yml)
![PYPI-DL](https://img.shields.io/pypi/dm/openadr3-client-gac-compliance?style=flat)
[![image](https://img.shields.io/pypi/v/openadr3-client-gac-compliance?label=pypi)](https://pypi.python.org/pypi/openadr3-client-gac-compliance)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FElaadNL%2Fopenadr3-client-gac-compliance%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

# OpenADR3 client

This repository contains a plugin for the [OpenADR3-client](https://github.com/ElaadNL/openadr3-client) library that adds additional Pydantic validators to the OpenADR3 domain models to ensure GAC compliance. Since GAC compliance is a superset of OpenADR3, adding validation rules on top of the OpenADR3 models is sufficient to ensure compliance.

Registering the plugin is done using the global ValidatorPluginRegistry class:

```python
from openadr3_client.plugin import ValidatorPluginRegistry, ValidatorPlugin
from openadr3_client_gac_compliance.gac20.plugin import Gac20ValidatorPlugin
from openadr3_client_gac_compliance.gac21.plugin import Gac21ValidatorPlugin
from openadr3_client_gac_compliance.gac22.plugin import Gac22ValidatorPlugin

ValidatorPluginRegistry.register_plugin(
    Gac21ValidatorPlugin().setup()  # Depending on which version of GAC you are testing, register either the GAC20, GAC21 or GAC22 plugin.
)
```

### GAC 2.2: raw-input checks

GAC 2.2 section 9.1.5 forbids days in durations (`P1D`, use `PT24H`) and requires timestamps in UTC with the `Z` notation, and OpenADR 3.1 defines timestamps as RFC 3339 strings and durations as ISO 8601 strings. The parser is more lenient: `P1D` and `PT24H` become the same `timedelta`, `Z` and `+00:00` the same `datetime`, and it also accepts plain numbers such as a Unix epoch timestamp or a number of seconds. These rules therefore cannot be checked on the parsed model, where the plugin validators run. Run the raw-input functions on the raw JSON before parsing it, and raise or report their errors:

```python
from pydantic import ValidationError
from openadr3_client_gac_compliance.gac22 import validate_raw_event

raw_event = response.json()  # the dict as returned by the VTN, not yet parsed
errors = validate_raw_event(raw_event)
if errors:
    raise ValidationError.from_exception_data("Event", errors)
```

`validate_raw_program` and `validate_raw_ven` work the same way. They are deliberately not registered in the plugin.

### Changes in GAC 2.2.0

gac22 now rejects:

- Targets without the `EAN` prefix (a bare 18 digits).
- Missing or empty event and VEN targets.
- A RETAILER_NAME that is not exactly one of the six DSO EAN13 codes.
- A PROGRAM_TYPE with more than one value.
- BINDING_EVENTS that is not literally `true`.
- An event in which any interval, not only the last, lacks an IMPORT_CAPACITY_LIMIT payload.
- Events whose intervals do not cover two local calendar days (Europe/Amsterdam).

gac22 now accepts:

- A `priority` on the event.
- Several payloads or values per interval.
- Several payload descriptors, as long as each is IMPORT_CAPACITY_LIMIT in KW.

New: the raw-input functions (`validate_raw_event`, `validate_raw_program`, `validate_raw_ven`), which callers run on the raw JSON before parsing.

## License

This project is licensed under the Apache-2.0 - see LICENSE for details.

## Licenses third-party libraries

This project includes third-party libraries, which are licensed under their own respective Open-Source licenses.
SPDX-License-Identifier headers are used to show which license is applicable. The concerning license files can be found in the LICENSES directory.

---

## About ElaadNL

OpenADRGUI is built by ElaadNL, with the goal of using it for both internal projects as well as those of stakeholders.

ElaadNL is a Dutch research institute founded and funded by the Dutch District Service Operators (DSOs). ElaadNL was originally tasked by the DSOs to kickstart and foster the adoption of Electric Vehicles by installing the first Dutch charging stations, as well as monitoring the effects EVs have on the grid.

A major result of this pioneering work, was the creation of the Open Charge Point Protocol (OCPP), which today is the de-facto standard for CPOs to communicate with and manage their chargepoints. The protocol is now managed in a spin-off organization: the Open Charge Alliance, which is still closely connected with ElaadNL.

Whereas ElaadNL initially focused mainly on EVs, it has now expanded its mandate to include residential energy use with the goal of increasing the adoption of demand response measures. The reason for this move is to improve efficient use of the resources of the DSO in order to reduce grid congestion, which is a major problem challenge for the Dutch DSOs as well as society as a whole.
