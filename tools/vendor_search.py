"""
Tool: vendor_search_similar
Semantic similarity search over vendor profiles using Pinecone + Gemini embeddings.
"""

import json
import sys
import logging
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class VendorSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query: str = Field(..., description="Natural language search query", min_length=1, max_length=500)
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=20)
    response_format: str = Field(default="markdown", description="Output format: 'markdown' or 'json'")


async def vendor_search_similar(params: VendorSearchInput) -> str:
    try:
        from utils.embeddings import get_embedding
        from utils.pinecone_client import get_pinecone_index
        from utils.supabase_client import get_supabase_client

        # Generate embedding for the query
        query_embedding = await get_embedding(params.query)

        # Search Pinecone
        index = get_pinecone_index()
        results = index.query(
            vector=query_embedding,
            top_k=params.top_k,
            include_metadata=True
        )

        if not results.matches:
            return "No similar vendors found for the given query."

        # Enrich with Supabase data
        supabase = get_supabase_client()
        enriched = []

        for match in results.matches:
            vendor_name = match.metadata.get("vendor_name", "Unknown")
            score = round(match.score, 4)

            # Fetch full record from Supabase
            db_result = supabase.table("vendors").select("*").ilike("name", vendor_name).execute()
            vendor_data = db_result.data[0] if db_result.data else {}

            enriched.append({
                "vendor_name": vendor_name,
                "similarity_score": score,
                "risk_score": vendor_data.get("risk_score"),
                "risk_category": vendor_data.get("risk_category"),
                "country": vendor_data.get("country"),
                "category": vendor_data.get("category"),
                "contract_value": vendor_data.get("contract_value")
            })

        if params.response_format == "json":
            return json.dumps({
                "query": params.query,
                "total_results": len(enriched),
                "results": enriched
            }, indent=2)

        # Markdown format
        lines = [
            f"## Similar Vendors — Query: *{params.query}*\n",
            f"Found **{len(enriched)}** result(s):\n"
        ]
        for i, v in enumerate(enriched, 1):
            risk_score = v.get("risk_score")
            risk_display = f"{risk_score}/100" if risk_score is not None else "N/A"
            contract = v.get("contract_value")
            contract_display = f"${contract:,.0f}" if contract else "N/A"

            lines.append(
                f"### {i}. {v['vendor_name']}\n"
                f"- **Similarity Score**: {v['similarity_score']}\n"
                f"- **Risk Score**: {risk_display} ({v.get('risk_category', 'N/A')})\n"
                f"- **Country**: {v.get('country', 'N/A')}\n"
                f"- **Category**: {v.get('category', 'N/A')}\n"
                f"- **Contract Value**: {contract_display}\n"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"vendor_search_similar error: {e}", exc_info=True)
        return f"Error searching vendors: {str(e)}"
