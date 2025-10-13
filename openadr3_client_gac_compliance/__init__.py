"""
OpenADR3 GAC Compliance Plugin.

This package provides validation plugins for OpenADR3 models to ensure compliance
with the Grid Aware Charging (GAC) specification.

The main entry point is the Gac20ValidatorPlugin which can be registered
with the OpenADR3 client's validator plugin registry.

Example:
    ```python
    from openadr3_client.plugin import ValidatorPluginRegistry
    from openadr3_client_gac_compliance.plugin import Gac20ValidatorPlugin
    from openadr3_client_gac_compliance.gac20.gac_plugin import GacVersion

    # Register the GAC validation plugin
    ValidatorPluginRegistry.register_plugin(
        Gac20ValidatorPlugin.setup(gac_version=GacVersion.VERSION_2_0)
    )
    ```

"""
