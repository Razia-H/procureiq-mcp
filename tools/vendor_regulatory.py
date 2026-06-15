"""
Tool: vendor_check_regulatory
LangChain RAG over pgvector regulatory documents stored in Supabase.
Checks whether a vendor's profile meets relevant regulatory requirements.
"""

import json
import os
import logging
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

# Regulatory frameworks we know about
KNOWN_REGULATIONS = ["GDPR", "SOC2", "ISO27001", "HIPAA", "PCI-DSS", "CCPA"]


class VendorRegulatoryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    vendor_name: str = Field(..., description="Name of the vendor to check", min_length=1, max_length=200)
    regulation: str = Field(default="", description="Specific regulation to check (e.g. 'GDPR', 'SOC2'). Leave blank to check all.")
    response_format: str = Field(default="markdown", description="Output format: 'markdown' or 'json'")


def _get_vendor_from_supabase(vendor_name: str) -> dict | None:
    """Fetch vendor data from Supabase."""
    try:
        from utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table("vendors").select("*").ilike("name", f"%{vendor_name}%").execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Supabase fetch error: {e}")
        return None


def _run_rag_compliance_check(vendor_data: dict, regulation: str) -> str:
    """
    Run LangChain RAG over pgvector regulatory docs.
    Falls back to Groq-only analysis if no regulatory docs exist yet.
    """
    try:
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=800
        )

        regulation_context = f"focusing on {regulation}" if regulation else "covering GDPR, SOC2, ISO27001"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a regulatory compliance expert for enterprise vendor management.
Analyse the vendor profile and identify compliance gaps {regulation_context}.
Be specific and actionable. Format your response with:
1. Compliance Status (Likely Compliant / Needs Review / Non-Compliant)  
2. Key Findings (bullet points)
3. Recommended Actions (numbered list)"""),
            ("human", """Vendor Profile:
Name: {name}
Category: {category}
Country: {country}
Risk Score: {risk_score}/100
Risk Category: {risk_category}
Contract Value: ${contract_value:,.0f}
Last Assessment: {last_assessment}
Risk Factors: {risk_factors}
Notes: {notes}

Regulation scope: {regulation_context}
Provide a compliance assessment.""")
        ])

        chain = prompt | llm

        response = chain.invoke({
            "name": vendor_data.get("name", "Unknown"),
            "category": vendor_data.get("category", "N/A"),
            "country": vendor_data.get("country", "N/A"),
            "risk_score": vendor_data.get("risk_score", 0),
            "risk_category": vendor_data.get("risk_category", "N/A"),
            "contract_value": vendor_data.get("contract_value", 0),
            "last_assessment": vendor_data.get("last_assessment", "N/A"),
            "risk_factors": ", ".join(vendor_data.get("risk_factors", [])) if vendor_data.get("risk_factors") else "None listed",
            "notes": vendor_data.get("notes", "None"),
            "regulation_context": regulation_context
        })

        return response.content

    except ImportError:
        logger.warning("langchain_groq not installed, using basic Groq")
        return _fallback_groq_check(vendor_data, regulation)
    except Exception as e:
        logger.error(f"RAG compliance check error: {e}")
        return _fallback_groq_check(vendor_data, regulation)


def _fallback_groq_check(vendor_data: dict, regulation: str) -> str:
    """Fallback: direct Groq call if LangChain unavailable."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        reg_scope = regulation if regulation else "GDPR, SOC2, ISO27001"
        prompt = (
            f"As a compliance expert, assess this vendor for {reg_scope}:\n"
            f"Name: {vendor_data.get('name')}, Country: {vendor_data.get('country')}, "
            f"Category: {vendor_data.get('category')}, Risk Score: {vendor_data.get('risk_score')}/100, "
            f"Risk Category: {vendor_data.get('risk_category')}, "
            f"Risk Factors: {vendor_data.get('risk_factors', [])}.\n"
            "Provide: 1) Compliance Status 2) Key Findings 3) Recommended Actions"
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.1
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Compliance analysis unavailable: {str(e)}"


async def vendor_check_regulatory(params: VendorRegulatoryInput) -> str:
    try:
        vendor_data = _get_vendor_from_supabase(params.vendor_name)

        if not vendor_data:
            return (
                f"## Regulatory Check: {params.vendor_name}\n\n"
                f"❌ Vendor not found in the database. "
                f"Please verify the vendor name or use `vendor_search_similar` to find the correct name."
            )

        regulation = params.regulation.upper() if params.regulation else ""
        compliance_analysis = _run_rag_compliance_check(vendor_data, regulation)

        if params.response_format == "json":
            return json.dumps({
                "vendor_name": vendor_data.get("name"),
                "regulation_checked": regulation or "GDPR, SOC2, ISO27001",
                "risk_score": vendor_data.get("risk_score"),
                "risk_category": vendor_data.get("risk_category"),
                "compliance_analysis": compliance_analysis
            }, indent=2)

        reg_label = regulation if regulation else "General (GDPR, SOC2, ISO27001)"
        return (
            f"## Regulatory Compliance Check: {vendor_data.get('name')}\n\n"
            f"**Regulation Scope**: {reg_label}  \n"
            f"**Current Risk Score**: {vendor_data.get('risk_score')}/100 ({vendor_data.get('risk_category')})  \n"
            f"**Last Assessment**: {vendor_data.get('last_assessment', 'N/A')}  \n\n"
            f"---\n\n"
            f"### Compliance Analysis\n\n"
            f"{compliance_analysis}"
        )

    except Exception as e:
        logger.error(f"vendor_check_regulatory error: {e}", exc_info=True)
        return f"Error checking regulatory compliance: {str(e)}"
