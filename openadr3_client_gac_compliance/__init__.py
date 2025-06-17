from openadr3_client_gac_compliance.config import GAC_VERSION

if GAC_VERSION == "2.0":
    import openadr3_client_gac_compliance.gac20.program_gac_compliant  # noqa: F401
    import openadr3_client_gac_compliance.gac20.event_gac_compliant  # noqa: F401
    import openadr3_client_gac_compliance.gac20.ven_gac_compliant  # noqa: F401
