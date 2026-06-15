"""
Tool: vendor_get_news
Fetch and summarise recent news about a vendor using DuckDuckGo search + Groq LLM.
No paid search API required — uses duckduckgo-search (already pip-installable).
"""

import json
import logging
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class VendorNewsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    vendor_name: str = Field(..., description="Name of the vendor to search news for", min_length=1, max_length=200)
    max_results: int = Field(default=5, description="Maximum number of news items to return", ge=1, le=10)
    response_format: str = Field(default="markdown", description="Output format: 'markdown' or 'json'")


def _search_news(vendor_name: str, max_results: int) -> list[dict]:
    """Search for vendor news using DuckDuckGo (no API key needed)."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(
                keywords=f"{vendor_name} company risk compliance news",
                max_results=max_results
            ))
        return results
    except ImportError:
        logger.warning("duckduckgo_search not installed, using fallback")
        return []
    except Exception as e:
        logger.error(f"News search error: {e}")
        return []


def _summarise_with_groq(vendor_name: str, articles: list[dict]) -> str:
    """Use Groq to summarise risk-relevant signals from the news articles."""
    try:
        import os
        from groq import Groq

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        articles_text = "\n\n".join([
            f"Title: {a.get('title', 'N/A')}\n"
            f"Date: {a.get('date', 'N/A')}\n"
            f"Source: {a.get('source', 'N/A')}\n"
            f"Body: {a.get('body', a.get('description', 'N/A'))}"
            for a in articles
        ])

        prompt = f"""You are a vendor risk analyst. Review the following news about "{vendor_name}" 
and provide a concise risk intelligence summary. Focus on: regulatory issues, financial health, 
security incidents, leadership changes, or reputational risks.

NEWS ARTICLES:
{articles_text}

Provide:
1. Overall risk signal (Increased / Stable / Decreased)
2. Key risk themes (bullet points)
3. Recommended action for procurement team (1-2 sentences)
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq summarisation error: {e}")
        return "AI summarisation unavailable."


async def vendor_get_news(params: VendorNewsInput) -> str:
    try:
        articles = _search_news(params.vendor_name, params.max_results)

        if not articles:
            return (
                f"## News for {params.vendor_name}\n\n"
                "No recent news found. This may indicate low public profile or a search connectivity issue.\n\n"
                "_Tip: Ensure `duckduckgo-search` is installed: `pip install duckduckgo-search`_"
            )

        # Groq AI risk summary
        ai_summary = _summarise_with_groq(params.vendor_name, articles)

        if params.response_format == "json":
            return json.dumps({
                "vendor_name": params.vendor_name,
                "article_count": len(articles),
                "ai_risk_summary": ai_summary,
                "articles": [
                    {
                        "title": a.get("title"),
                        "date": a.get("date"),
                        "source": a.get("source"),
                        "url": a.get("url"),
                        "summary": a.get("body", a.get("description", ""))[:300]
                    }
                    for a in articles
                ]
            }, indent=2)

        # Markdown format
        lines = [
            f"## News Intelligence: {params.vendor_name}\n",
            "### 🤖 AI Risk Summary",
            ai_summary,
            "\n---\n",
            f"### 📰 Recent Articles ({len(articles)} found)\n"
        ]

        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            date = article.get("date", "Unknown date")
            source = article.get("source", "Unknown source")
            url = article.get("url", "")
            body = article.get("body", article.get("description", ""))[:250]

            lines.append(
                f"**{i}. [{title}]({url})**\n"
                f"*{source} — {date}*\n"
                f"{body}...\n"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"vendor_get_news error: {e}", exc_info=True)
        return f"Error fetching news for {params.vendor_name}: {str(e)}"
