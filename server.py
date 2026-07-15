import os
import sys
import logging
from dotenv import load_dotenv

# Suppress ALL stdout before anything else — stdout is the JSON-RPC channel
# Any stray print() will corrupt the MCP stream and break Claude Desktop
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

load_dotenv()

from mcp.server.fastmcp import FastMCP
from tools.vendor_profile import VendorGetProfileInput, vendor_get_profile
from tools.vendor_search import VendorSearchInput, vendor_search_similar
from tools.vendor_news import VendorNewsInput, vendor_get_news
from tools.vendor_contracts import VendorContractsInput, vendor_list_contracts
from tools.vendor_regulatory import VendorRegulatoryInput, vendor_check_regulatory
from tools.vendor_risk_delta import VendorRiskDeltaInput, vendor_analyze_risk_delta
from tools.vendor_generate_report import VendorGenerateReportInput, vendor_generate_report

mcp = FastMCP("procureiq_mcp")


# ─────────────────────────────────────────────
# Tool 1: vendor_get_profile
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_get_profile",
    annotations={
        "title": "Get Vendor Risk Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_vendor_get_profile(
    vendor_name: str,
    response_format: str = "markdown"
) -> str:
    """
    Retrieve the full risk profile for a vendor by name.
    Returns risk score, category, country, contract value,
    last assessment date, risk factors and notes.

    Args:
        vendor_name: Name of the vendor to look up (e.g. 'TechCorp Solutions')
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Full vendor risk profile with risk score and factors
    """
    params = VendorGetProfileInput(
        vendor_name=vendor_name,
        response_format=response_format
    )
    return await vendor_get_profile(params)


# ─────────────────────────────────────────────
# Tool 2: vendor_search_similar
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_search_similar",
    annotations={
        "title": "Search Similar Vendors",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_vendor_search_similar(
    query: str,
    top_k: int = 5,
    response_format: str = "markdown"
) -> str:
    """
    Search for vendors semantically similar to a natural-language query.
    Uses Pinecone vector search over vendor profiles.

    Args:
        query: Natural language description (e.g. 'cloud storage vendors in Europe with low risk')
        top_k: Number of results to return (1-20, default 5)
        response_format: Output format - 'markdown' or 'json'

    Returns:
        List of matching vendors with similarity scores and risk summaries
    """
    params = VendorSearchInput(
        query=query,
        top_k=top_k,
        response_format=response_format
    )
    return await vendor_search_similar(params)


# ─────────────────────────────────────────────
# Tool 3: vendor_get_news
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_get_news",
    annotations={
        "title": "Get Vendor News",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def tool_vendor_get_news(
    vendor_name: str,
    max_results: int = 5,
    response_format: str = "markdown"
) -> str:
    """
    Fetch recent news articles about a vendor using web search.
    Useful for identifying emerging risks, regulatory actions, or reputation events.

    Args:
        vendor_name: Name of the vendor (e.g. 'DataBridge Ltd')
        max_results: Maximum number of news items to return (1-10, default 5)
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Recent news headlines and summaries related to the vendor
    """
    params = VendorNewsInput(
        vendor_name=vendor_name,
        max_results=max_results,
        response_format=response_format
    )
    return await vendor_get_news(params)


# ─────────────────────────────────────────────
# Tool 4: vendor_check_regulatory
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_check_regulatory",
    annotations={
        "title": "Check Vendor Regulatory Compliance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_vendor_check_regulatory(
    vendor_name: str,
    regulation: str = "",
    response_format: str = "markdown"
) -> str:
    """
    Check a vendor's regulatory compliance using RAG over stored regulatory documents.
    Searches pgvector embeddings for relevant compliance requirements and flags gaps.

    Args:
        vendor_name: Name of the vendor to check (e.g. 'CloudBase Inc')
        regulation: Specific regulation to check (e.g. 'GDPR', 'SOC2', 'ISO27001') - optional
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Regulatory compliance assessment with matched requirements and gap analysis
    """
    params = VendorRegulatoryInput(
        vendor_name=vendor_name,
        regulation=regulation,
        response_format=response_format
    )
    return await vendor_check_regulatory(params)


# ─────────────────────────────────────────────
# Tool 5: vendor_list_contracts
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_list_contracts",
    annotations={
        "title": "List Vendor Contracts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_vendor_list_contracts(
    risk_category: str = "",
    country: str = "",
    min_contract_value: float = 0,
    limit: int = 10,
    offset: int = 0,
    response_format: str = "markdown"
) -> str:
    """
    List vendor contracts with optional filtering and pagination.
    Supports filtering by risk category, country, and minimum contract value.

    Args:
        risk_category: Filter by risk level - 'Low', 'Medium', 'High', 'Critical' (optional)
        country: Filter by vendor country (e.g. 'USA', 'UK') (optional)
        min_contract_value: Minimum contract value in USD (default 0)
        limit: Results per page (1-50, default 10)
        offset: Pagination offset (default 0)
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Paginated list of vendor contracts with risk scores and values
    """
    params = VendorContractsInput(
        risk_category=risk_category,
        country=country,
        min_contract_value=min_contract_value,
        limit=limit,
        offset=offset,
        response_format=response_format
    )
    return await vendor_list_contracts(params)


# ─────────────────────────────────────────────
# Tool 6: vendor_analyze_risk_delta
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_analyze_risk_delta",
    annotations={
        "title": "Analyze Vendor Risk Delta",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def tool_vendor_analyze_risk_delta(
    vendor_name: str,
    response_format: str = "markdown"
) -> str:
    """
    Detect risk drift for a vendor by combining stored profile data with recent news.
    Uses a LangGraph stateful agent to compare baseline risk vs current signals
    and produce a risk delta report with recommended actions.

    Args:
        vendor_name: Name of the vendor to analyze (e.g. 'SecureNet Systems')
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Risk delta report showing score change, drift drivers, and recommended actions
    """
    params = VendorRiskDeltaInput(
        vendor_name=vendor_name,
        response_format=response_format
    )
    return await vendor_analyze_risk_delta(params)


# ─────────────────────────────────────────────
# Tool 7: vendor_generate_report
# ─────────────────────────────────────────────
@mcp.tool(
    name="vendor_generate_report",
    annotations={
        "title": "Generate Executive Vendor Risk Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def tool_vendor_generate_report(
    vendor_name: str,
    include_news: bool = True,
    include_regulatory: bool = True,
    response_format: str = "markdown"
) -> str:
    """
    Generate an executive-ready risk report for a vendor, combining
    the stored profile with recent news signal and regulatory
    compliance status into one shareable summary.

    Args:
        vendor_name: Name of the vendor to report on (e.g. 'DataBridge Ltd')
        include_news: Whether to include a recent news / risk signal section (default True)
        include_regulatory: Whether to include a regulatory compliance section (default True)
        response_format: Output format - 'markdown' or 'json'

    Returns:
        Executive risk report combining profile, news signal, and compliance status
    """
    params = VendorGenerateReportInput(
        vendor_name=vendor_name,
        include_news=include_news,
        include_regulatory=include_regulatory,
        response_format=response_format
    )
    return await vendor_generate_report(params)


# ─────────────────────────────────────────────
# Entry point — runs unconditionally so Claude
# Desktop can spawn this as a subprocess cleanly
# ─────────────────────────────────────────────
mcp.run(transport="stdio")