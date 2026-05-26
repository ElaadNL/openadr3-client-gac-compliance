# SPDX-FileCopyrightText: Contributors to openadr3-client-gac-compliance <https://github.com/ElaadNL/openadr3-client-gac-compliance>
#
# SPDX-License-Identifier: Apache-2.0

"""GAC 2.1 compliance plugin for OpenADR3 client."""

from typing import Any

from openadr3_client.oadr310.models.event.event import Event
from openadr3_client.oadr310.models.program.program import Program
from openadr3_client.oadr310.models.ven.ven import Ven
from openadr3_client.plugin import ValidatorPlugin

from openadr3_client_gac_compliance.gac21.event_gac_compliant import validate_event_gac_compliant
from openadr3_client_gac_compliance.gac21.program_gac_compliant import validate_program_gac_compliant
from openadr3_client_gac_compliance.gac21.ven_gac_compliant import validate_ven_gac_compliant


class Gac21ValidatorPlugin(ValidatorPlugin):
    """Plugin that validates OpenADR3 models for GAC 2.1 compliance."""

    def __init__(self) -> None:
        """Initialize the GAC validator plugin."""
        super().__init__()

    @staticmethod
    def setup(*_args: Any, **_kwargs: Any) -> "Gac21ValidatorPlugin":  # noqa: ANN401
        """
        Set up the GAC validator plugin.

        Args:
            *args: Positional arguments (unused).
            **kwargs: Keyword arguments containing configuration.
                     Expected keys:
                     - gac_version: The GAC version to validate against.

        Returns:
            GacValidatorPlugin: Configured plugin instance.

        """
        plugin = Gac21ValidatorPlugin()

        plugin.register_model_validator(Event, validate_event_gac_compliant)
        plugin.register_model_validator(Program, validate_program_gac_compliant)
        plugin.register_model_validator(Ven, validate_ven_gac_compliant)

        return plugin
