# OpenADR3 client

This repository contains a plugin for the [OpenADR3-client](https://github.com/ElaadNL/openadr3-client) library that adds additional pydantic validators to the OpenADR3 domain models to ensure GAC compliance. Since GAC compliance is a superset of OpenADR3, adding validation rules on top of the OpenADR3 models is sufficient to ensure compliance.

To use this plugin, the package must be imported once globally. We recommend doing this in your root directories `__init__.py` file.

```python
import openadr3_client_gac_compliance  # noqa: F401 (in case you use ruff)
```