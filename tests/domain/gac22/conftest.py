# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterator

import pytest
from openadr3_client.plugin import ValidatorPluginRegistry

from openadr3_client_gac_compliance.gac22.plugin import Gac22ValidatorPlugin


@pytest.fixture(autouse=True)
def gac22_plugin_registered() -> Iterator[None]:
    """Register only the GAC 2.2 plugin for the duration of each test."""
    ValidatorPluginRegistry.clear_plugins()
    ValidatorPluginRegistry.register_plugin(Gac22ValidatorPlugin.setup())
    yield
    ValidatorPluginRegistry.clear_plugins()
