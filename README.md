<!--
SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>

SPDX-License-Identifier: Apache-2.0
-->

# OpenADR3 client

This repository contains a plugin for the [OpenADR3-client](https://github.com/ElaadNL/openadr3-client) library that adds additional Pydantic validators to the OpenADR3 domain models to ensure GAC compliance. Since GAC compliance is a superset of OpenADR3, adding validation rules on top of the OpenADR3 models is sufficient to ensure compliance.

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

---

## About ElaadNL

OpenADRGUI is built by ElaadNL, with the goal of using it for both internal projects as well as those of stakeholders.

ElaadNL is a Dutch research institute founded and funded by the Dutch District Service Operators (DSOs). ElaadNL was originally tasked by the DSOs to kickstart and foster the adoption of Electric Vehicles by installing the first Dutch charging stations, as well as monitoring the effects EVs have on the grid.

A major result of this pioneering work, was the creation of the Open Charge Point Protocol (OCPP), which today is the de-facto standard for CPOs to communicate with and manage their chargepoints. The protocol is now managed in a spin-off organization: the Open Charge Alliance, which is still closely connected with ElaadNL.

Whereas ElaadNL initially focused mainly on EVs, it has now expanded its mandate to include residential energy use with the goal of increasing the adoption of demand response measures. The reason for this move is to improve efficient use of the resources of the DSO in order to reduce grid congestion, which is a major problem challenge for the Dutch DSOs as well as society as a whole.
