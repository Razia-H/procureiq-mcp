"""
Tool: vendor_analyze_risk_delta
LangGraph stateful agent that detects risk drift by comparing
stored vendor baseline against current news signals.
"""

import json
import os
import logging
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class VendorRiskDeltaInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    vendor_name: str = Field(..., description="Name of the vendor to analyse for risk drift", min_length=1, max_length=200)
    response_format: str = Field(default="markdown", description="Output format: 'markdown' or 'json'")


# ─── LangGraph state schema ───────────────────────────────────────────────────

class RiskDeltaState(TypedDict):
    vendor_name: str
    baseline_profile: dict
    news_articles: list
    news_summary: str
    baseline_risk_score: int
    current_risk_signal: str   # "Increased" | "Stable" | "Decreased"
    delta_score: int           # estimated score change (-100 to +100)
    drift_drivers: list
    recommended_actions: list
    final_report: str


# ─── Individual agent nodes ────────────────────────────────────────────────────

def _node_fetch_baseline(state: RiskDeltaState) -> RiskDeltaState:
    """Node 1: Fetch vendor baseline from Supabase."""
    try:
        from utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table("vendors").select("*").ilike("name", f"%{state['vendor_name']}%").execute()
        profile = result.data[0] if result.data else {}
        return {
            **state,
            "baseline_profile": profile,
            "baseline_risk_score": profile.get("risk_score", 50)
        }
    except Exception as e:
        logger.error(f"Baseline fetch error: {e}")
        return {**state, "baseline_profile": {}, "baseline_risk_score": 50}


def _node_fetch_news(state: RiskDeltaState) -> RiskDeltaState:
    """Node 2: Fetch recent news about the vendor."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            articles = list(ddgs.news(
                keywords=f"{state['vendor_name']} risk compliance news",
                max_results=5
            ))
        return {**state, "news_articles": articles}
    except Exception as e:
        logger.warning(f"News fetch error (non-fatal): {e}")
        return {**state, "news_articles": []}


def _node_analyse_delta(state: RiskDeltaState) -> RiskDeltaState:
    """Node 3: Groq LLM analyses risk delta between baseline and news."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        profile = state["baseline_profile"]
        articles_text = "\n".join([
            f"- {a.get('title', '')} ({a.get('date', '')}): {a.get('body', a.get('description', ''))[:200]}"
            for a in state["news_articles"]
        ]) if state["news_articles"] else "No recent news found."

        prompt = f"""You are a senior vendor risk analyst. Analyse risk drift for this vendor.

BASELINE PROFILE:
- Name: {profile.get('name', state['vendor_name'])}
- Current Risk Score: {state['baseline_risk_score']}/100
- Risk Category: {profile.get('risk_category', 'N/A')}
- Country: {profile.get('country', 'N/A')}
- Category: {profile.get('category', 'N/A')}
- Known Risk Factors: {profile.get('risk_factors', [])}
- Last Assessment: {profile.get('last_assessment', 'N/A')}

RECENT NEWS SIGNALS:
{articles_text}

Respond ONLY with valid JSON in this exact format:
{{
  "current_risk_signal": "Increased|Stable|Decreased",
  "delta_score": <integer from -30 to +30>,
  "drift_drivers": ["driver1", "driver2"],
  "recommended_actions": ["action1", "action2"],
  "news_summary": "2-3 sentence summary of news risk signals"
}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()
        # Extract JSON even if wrapped in markdown fences
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        analysis = json.loads(raw.strip())

        return {
            **state,
            "current_risk_signal": analysis.get("current_risk_signal", "Stable"),
            "delta_score": analysis.get("delta_score", 0),
            "drift_drivers": analysis.get("drift_drivers", []),
            "recommended_actions": analysis.get("recommended_actions", []),
            "news_summary": analysis.get("news_summary", "")
        }

    except Exception as e:
        logger.error(f"Delta analysis error: {e}")
        return {
            **state,
            "current_risk_signal": "Stable",
            "delta_score": 0,
            "drift_drivers": ["Analysis unavailable"],
            "recommended_actions": ["Manual review recommended"],
            "news_summary": f"Analysis error: {str(e)}"
        }


def _node_build_report(state: RiskDeltaState) -> RiskDeltaState:
    """Node 4: Build the final delta report string."""
    profile = state["baseline_profile"]
    vendor_name = profile.get("name", state["vendor_name"])
    baseline = state["baseline_risk_score"]
    delta = state["delta_score"]
    new_score = max(0, min(100, baseline + delta))

    signal_emoji = {"Increased": "🔴", "Stable": "🟡", "Decreased": "🟢"}.get(
        state["current_risk_signal"], "🟡"
    )

    drivers_md = "\n".join(f"- {d}" for d in state["drift_drivers"]) or "- No significant drivers detected"
    actions_md = "\n".join(f"{i+1}. {a}" for i, a in enumerate(state["recommended_actions"])) or "1. No actions required"

    report = (
        f"## Risk Delta Report: {vendor_name}\n\n"
        f"### {signal_emoji} Risk Signal: {state['current_risk_signal']}\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Baseline Risk Score | {baseline}/100 |\n"
        f"| Estimated Delta | {'+' if delta >= 0 else ''}{delta} pts |\n"
        f"| Projected Risk Score | **{new_score}/100** |\n"
        f"| Country | {profile.get('country', 'N/A')} |\n"
        f"| Category | {profile.get('category', 'N/A')} |\n\n"
        f"### 📊 News Signal Summary\n{state['news_summary']}\n\n"
        f"### ⚠️ Drift Drivers\n{drivers_md}\n\n"
        f"### ✅ Recommended Actions\n{actions_md}\n\n"
        f"*Analysis based on {len(state['news_articles'])} recent news article(s).*"
    )

    return {**state, "final_report": report}


def _run_langgraph_pipeline(vendor_name: str) -> RiskDeltaState:
    """Run the LangGraph pipeline. Falls back to sequential if LangGraph unavailable."""
    try:
        from langgraph.graph import StateGraph, END
        import operator

        builder = StateGraph(RiskDeltaState)
        builder.add_node("fetch_baseline", _node_fetch_baseline)
        builder.add_node("fetch_news", _node_fetch_news)
        builder.add_node("analyse_delta", _node_analyse_delta)
        builder.add_node("build_report", _node_build_report)

        builder.set_entry_point("fetch_baseline")
        builder.add_edge("fetch_baseline", "fetch_news")
        builder.add_edge("fetch_news", "analyse_delta")
        builder.add_edge("analyse_delta", "build_report")
        builder.add_edge("build_report", END)

        graph = builder.compile()
        initial_state: RiskDeltaState = {
            "vendor_name": vendor_name,
            "baseline_profile": {},
            "news_articles": [],
            "news_summary": "",
            "baseline_risk_score": 50,
            "current_risk_signal": "Stable",
            "delta_score": 0,
            "drift_drivers": [],
            "recommended_actions": [],
            "final_report": ""
        }
        return graph.invoke(initial_state)

    except ImportError:
        logger.warning("langgraph not installed — running sequential fallback")
        state: RiskDeltaState = {
            "vendor_name": vendor_name,
            "baseline_profile": {},
            "news_articles": [],
            "news_summary": "",
            "baseline_risk_score": 50,
            "current_risk_signal": "Stable",
            "delta_score": 0,
            "drift_drivers": [],
            "recommended_actions": [],
            "final_report": ""
        }
        state = _node_fetch_baseline(state)
        state = _node_fetch_news(state)
        state = _node_analyse_delta(state)
        state = _node_build_report(state)
        return state


async def vendor_analyze_risk_delta(params: VendorRiskDeltaInput) -> str:
    try:
        final_state = _run_langgraph_pipeline(params.vendor_name)

        if params.response_format == "json":
            return json.dumps({
                "vendor_name": params.vendor_name,
                "baseline_risk_score": final_state["baseline_risk_score"],
                "delta_score": final_state["delta_score"],
                "projected_score": max(0, min(100, final_state["baseline_risk_score"] + final_state["delta_score"])),
                "current_risk_signal": final_state["current_risk_signal"],
                "drift_drivers": final_state["drift_drivers"],
                "recommended_actions": final_state["recommended_actions"],
                "news_summary": final_state["news_summary"],
                "articles_analysed": len(final_state["news_articles"])
            }, indent=2)

        return final_state["final_report"]

    except Exception as e:
        logger.error(f"vendor_analyze_risk_delta error: {e}", exc_info=True)
        return f"Error analysing risk delta for {params.vendor_name}: {str(e)}"
