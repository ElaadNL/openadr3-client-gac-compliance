from openadr3_client_gac_compliance.config import GAC_VERSION

if GAC_VERSION == "3.0":
    import openadr3_client_gac_compliance.gac30.program_gac_compliant  # noqa: F401
    import openadr3_client_gac_compliance.gac30.event_gac_compliant  # noqa: F401
