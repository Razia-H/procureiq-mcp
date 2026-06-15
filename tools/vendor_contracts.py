"""
Tool: vendor_list_contracts
List vendor contracts from Supabase with filtering and pagination.
"""

import json
import logging
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

VALID_RISK_CATEGORIES = {"Low", "Medium", "High", "Critical"}


class VendorContractsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    risk_category: str = Field(default="", description="Filter by risk level: 'Low', 'Medium', 'High', 'Critical'")
    country: str = Field(default="", description="Filter by vendor country (e.g. 'USA', 'UK')")
    min_contract_value: float = Field(default=0, description="Minimum contract value in USD", ge=0)
    limit: int = Field(default=10, description="Results per page", ge=1, le=50)
    offset: int = Field(default=0, description="Pagination offset", ge=0)
    response_format: str = Field(default="markdown", description="Output format: 'markdown' or 'json'")


async def vendor_list_contracts(params: VendorContractsInput) -> str:
    try:
        from utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()

        # Build query
        query = supabase.table("vendors").select(
            "name, risk_score, risk_category, country, category, contract_value, last_assessment",
            count="exact"
        )

        # Apply filters
        if params.risk_category and params.risk_category in VALID_RISK_CATEGORIES:
            query = query.eq("risk_category", params.risk_category)
        elif params.risk_category and params.risk_category not in VALID_RISK_CATEGORIES:
            return (
                f"Invalid risk_category '{params.risk_category}'. "
                f"Valid values: {', '.join(sorted(VALID_RISK_CATEGORIES))}"
            )

        if params.country:
            query = query.ilike("country", f"%{params.country}%")

        if params.min_contract_value > 0:
            query = query.gte("contract_value", params.min_contract_value)

        # Apply pagination
        query = query.order("risk_score", desc=True).range(
            params.offset, params.offset + params.limit - 1
        )

        result = query.execute()
        vendors = result.data or []
        total = result.count or 0
        has_more = total > params.offset + len(vendors)
        next_offset = params.offset + len(vendors) if has_more else None

        if not vendors:
            filters_desc = _describe_filters(params)
            return f"No vendors found{filters_desc}."

        if params.response_format == "json":
            return json.dumps({
                "total": total,
                "count": len(vendors),
                "offset": params.offset,
                "limit": params.limit,
                "has_more": has_more,
                "next_offset": next_offset,
                "filters": {
                    "risk_category": params.risk_category or None,
                    "country": params.country or None,
                    "min_contract_value": params.min_contract_value or None
                },
                "vendors": vendors
            }, indent=2)

        # Markdown format
        filters_desc = _describe_filters(params)
        page_info = f"Showing {params.offset + 1}–{params.offset + len(vendors)} of {total}"

        lines = [
            f"## Vendor Contracts{filters_desc}\n",
            f"*{page_info}*\n",
            "| # | Vendor | Risk Score | Category | Country | Contract Value | Last Assessment |",
            "|---|--------|-----------|---------|---------|----------------|-----------------|"
        ]

        for i, v in enumerate(vendors, params.offset + 1):
            contract = v.get("contract_value")
            contract_str = f"${contract:,.0f}" if contract else "N/A"
            lines.append(
                f"| {i} | {v.get('name', 'N/A')} | {v.get('risk_score', 'N/A')}/100 | "
                f"{v.get('risk_category', 'N/A')} | {v.get('country', 'N/A')} | "
                f"{contract_str} | {v.get('last_assessment', 'N/A')} |"
            )

        if has_more:
            lines.append(
                f"\n*{total - params.offset - len(vendors)} more vendor(s) available. "
                f"Use `offset={next_offset}` to see the next page.*"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"vendor_list_contracts error: {e}", exc_info=True)
        return f"Error listing contracts: {str(e)}"


def _describe_filters(params: VendorContractsInput) -> str:
    """Build a human-readable filter description."""
    parts = []
    if params.risk_category:
        parts.append(f"Risk: {params.risk_category}")
    if params.country:
        parts.append(f"Country: {params.country}")
    if params.min_contract_value:
        parts.append(f"Min Value: ${params.min_contract_value:,.0f}")
    return f" — Filters: {', '.join(parts)}" if parts else ""
