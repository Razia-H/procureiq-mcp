import json
import os
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.supabase_client import get_supabase
from utils.error_handlers import handle_error

class VendorGetProfileInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    vendor_name: str = Field(
        ...,
        description="Name of the vendor to look up (e.g. 'Acme Corp', 'TechSupplier Ltd')",
        min_length=1,
        max_length=100
    )
    response_format: Optional[str] = Field(
        default="markdown",
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

async def vendor_get_profile(params: VendorGetProfileInput) -> str:
    """
    Retrieve the full risk profile for a vendor by name.

    Returns vendor details including risk score, category, country,
    contract value, last assessment date, and risk factors.

    Args:
        params: VendorGetProfileInput with vendor_name and response_format

    Returns:
        str: Vendor profile in markdown or JSON format
    """
    try:
        supabase = get_supabase()
        result = supabase.table("vendors") \
            .select("*") \
            .ilike("name", f"%{params.vendor_name}%") \
            .limit(1) \
            .execute()

        if not result.data:
            return f"No vendor found matching '{params.vendor_name}'. Try a different name or use vendor_search_similar to find related vendors."

        vendor = result.data[0]

        if params.response_format == "json":
            return json.dumps(vendor, indent=2)

        risk_score = vendor.get("risk_score", 0)
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return f"""## Vendor Profile: {vendor.get("name")}

**Risk Score:** {risk_score}/100 — {risk_level} RISK
**Category:** {vendor.get("category", "N/A")}
**Country:** {vendor.get("country", "N/A")}
**Contract Value:** ${vendor.get("contract_value", 0):,}
**Last Assessment:** {vendor.get("last_assessment_date", "N/A")}
**Status:** {vendor.get("status", "N/A")}

### Risk Factors
{vendor.get("risk_factors", "No risk factors recorded")}

### Notes
{vendor.get("notes", "No additional notes")}
"""

    except Exception as e:
        return handle_error("vendor_get_profile", e)
