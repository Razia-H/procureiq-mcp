"""
Tool: vendor_generate_report
Synthesizes an executive-ready risk report for a vendor by combining
the stored profile, recent news signal, and regulatory compliance
status into a single structured summary.

Reuses existing fetch/analysis logic from vendor_profile, vendor_news,
and vendor_regulatory rather than duplicating it.
"""

import json
import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from utils.supabase_client import get_supabase_client
from utils.error_handlers import handle_error
from tools.vendor_news import _search_news, _summarise_with_groq
from tools.vendor_regulatory import _run_rag_compliance_check

logger = logging.getLogger(__name__)


class VendorGenerateReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    vendor_name: str = Field(
        ...,
        description="Name of the vendor to generate a report for (e.g. 'DataBridge Ltd')",
        min_length=1,
        max_length=200
    )
    include_news: bool = Field(
        default=True,
        description="Whether to include a recent news / risk signal section"
    )
    include_regulatory: bool = Field(
        default=True,
        description="Whether to include a regulatory compliance section"
    )
    response_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'"
    )


def _get_vendor(vendor_name: str) -> dict | None:
    """Fetch vendor data from Supabase by fuzzy name match."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("vendors").select("*").ilike("name", f"%{vendor_name}%").limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Vendor fetch error: {e}")
        return None


def _risk_level(risk_score: int) -> str:
    if risk_score >= 70:
        return "HIGH"
    elif risk_score >= 40:
        return "MEDIUM"
    return "LOW"


async def vendor_generate_report(params: VendorGenerateReportInput) -> str:
    """
    Generate an executive-ready risk report for a vendor.

    Combines the stored risk profile with optional recent-news signal
    and regulatory compliance analysis into one report suitable for
    sharing with stakeholders (procurement, compliance, leadership).

    Args:
        params: VendorGenerateReportInput with vendor_name and section toggles

    Returns:
        str: Executive risk report in markdown or JSON format
    """
    try:
        vendor = _get_vendor(params.vendor_name)

        if not vendor:
            return (
                f"## Executive Risk Report: {params.vendor_name}\n\n"
                f"Vendor not found. Try `vendor_search_similar` to find the correct name."
            )

        risk_score = vendor.get("risk_score", 0)
        risk_level = _risk_level(risk_score)
        generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y")

        news_summary = None
        if params.include_news:
            articles = _search_news(vendor.get("name"), max_results=5)
            news_summary = _summarise_with_groq(vendor.get("name"), articles) if articles else \
                "No recent news found for this vendor."

        regulatory_summary = None
        if params.include_regulatory:
            regulatory_summary = _run_rag_compliance_check(vendor, "")

        if params.response_format == "json":
            return json.dumps({
                "vendor_name": vendor.get("name"),
                "generated_at": generated_at,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "category": vendor.get("category"),
                "country": vendor.get("country"),
                "contract_value": vendor.get("contract_value"),
                "news_summary": news_summary,
                "regulatory_summary": regulatory_summary
            }, indent=2)

        lines = [
            f"# Executive Risk Report: {vendor.get('name')}",
            f"*Generated {generated_at}*\n",
            "---\n",
            "## Summary",
            f"**Risk Score:** {risk_score}/100 — {risk_level} RISK  ",
            f"**Category:** {vendor.get('category', 'N/A')}  ",
            f"**Country:** {vendor.get('country', 'N/A')}  ",
            f"**Contract Value:** ${vendor.get('contract_value', 0):,}  ",
            f"**Last Assessment:** {vendor.get('last_assessment_date', 'N/A')}  ",
            f"**Status:** {vendor.get('status', 'N/A')}\n",
        ]

        if vendor.get("risk_factors"):
            lines.append("### Known Risk Factors")
            lines.append(f"{vendor.get('risk_factors')}\n")

        if news_summary:
            lines.append("---\n")
            lines.append("## Recent Signal (News)")
            lines.append(f"{news_summary}\n")

        if regulatory_summary:
            lines.append("---\n")
            lines.append("## Regulatory Compliance")
            lines.append(f"{regulatory_summary}\n")

        lines.append("---\n")
        lines.append(
            "_This report was generated by ProcureIQ. Verify critical findings "
            "against source data before making procurement decisions._"
        )

        return "\n".join(lines)

    except Exception as e:
        return handle_error("vendor_generate_report", e)
