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

This repository contains a plugin for the [OpenADR3-client](https://github.com/ElaadNL/openadr3-client) library that adds additional pydantic validators to the OpenADR3 domain models to ensure GAC compliance. Since GAC compliance is a superset of OpenADR3, adding validation rules on top of the OpenADR3 models is sufficient to ensure compliance.

Registering the plugin is done using the global ValidatorPluginRegistry class:

```python
    from openadr3_client.plugin import ValidatorPluginRegistry, ValidatorPlugin
    from openadr3_client_gac_compliance.gac20.plugin import Gac20ValidatorPlugin

    ValidatorPluginRegistry.register_plugin(
        Gac20ValidatorPlugin().setup()
    )
```

## License

This project is licensed under the Apache-2.0 - see LICENSE for details.

## Licenses third-party libraries

This project includes third-party libraries, which are licensed under their own respective Open-Source licenses.
SPDX-License-Identifier headers are used to show which license is applicable. The concerning license files can be found in the LICENSES directory.
