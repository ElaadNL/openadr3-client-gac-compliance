"""GAC compliance plugin for OpenADR3 client."""

from typing import Any

from openadr3_client.models.event.event import Event
from openadr3_client.models.program.program import Program
from openadr3_client.models.ven.ven import Ven
from openadr3_client.plugin import ValidatorPlugin

from openadr3_client_gac_compliance.gac20.event_gac_compliant import validate_event_gac_compliant
from openadr3_client_gac_compliance.gac20.program_gac_compliant import validate_program_gac_compliant
from openadr3_client_gac_compliance.gac20.ven_gac_compliant import validate_ven_gac_compliant


class Gac20ValidatorPlugin(ValidatorPlugin):
    """Plugin that validates OpenADR3 models for GAC compliance."""

    def __init__(self) -> None:
        """Initialize the GAC validator plugin."""
        super().__init__()

    @staticmethod
    def setup(*_args: Any, **_kwargs: Any) -> "Gac20ValidatorPlugin":  # noqa: ANN401
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
        plugin = Gac20ValidatorPlugin()

        plugin.register_model_validator(Event, validate_event_gac_compliant)
        plugin.register_model_validator(Program, validate_program_gac_compliant)
        plugin.register_model_validator(Ven, validate_ven_gac_compliant)

        return plugin
