"""Contains configuration variables used by the OpenADR3 GAC compliance plugin."""

from decouple import config

VALID_GAC_VERSIONS: list[str] = ["2.0"]


def _gac_version_cast(value: str) -> str:
    """Cast the GAC version to a string.

    Args:
        value (str): The GAC version to cast.

    Raises:
        ValueError: If the GAC version is not a valid GAC version.

    Returns:
        str: The GAC version.
    """
    if value not in VALID_GAC_VERSIONS:
        raise ValueError(f"Invalid GAC version: {value}")
    return value


# The GAC version to use for the compliance validators.
GAC_VERSION = config("GAC_VERSION", default="2.0", cast=_gac_version_cast)
