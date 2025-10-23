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