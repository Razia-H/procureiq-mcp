from unittest.mock import patch, MagicMock
from tools.vendor_news import VendorNewsInput, vendor_get_news


async def test_returns_markdown_with_ai_summary(sample_news_articles):
    with patch("tools.vendor_news._search_news", return_value=sample_news_articles), \
         patch("tools.vendor_news._summarise_with_groq", return_value="Overall risk signal: Increased."):

        result = await vendor_get_news(VendorNewsInput(vendor_name="DataBridge Ltd"))

    assert "DataBridge Ltd" in result
    assert "Overall risk signal: Increased." in result
    assert "GDPR inquiry" in result


async def test_no_articles_returns_friendly_message():
    with patch("tools.vendor_news._search_news", return_value=[]):
        result = await vendor_get_news(VendorNewsInput(vendor_name="ObscureVendor"))

    assert "No recent news found" in result


async def test_json_format_includes_all_articles(sample_news_articles):
    import json
    with patch("tools.vendor_news._search_news", return_value=sample_news_articles), \
         patch("tools.vendor_news._summarise_with_groq", return_value="Stable."):

        result = await vendor_get_news(
            VendorNewsInput(vendor_name="DataBridge Ltd", response_format="json")
        )

    parsed = json.loads(result)
    assert parsed["article_count"] == 2
    assert len(parsed["articles"]) == 2


def test_search_news_returns_empty_list_on_failure():
    """_search_news should degrade gracefully (return []) rather than
    raise, whether the failure is a missing package or a network error —
    vendor_get_news depends on this to show its 'no news found' message
    instead of crashing."""
    from tools.vendor_news import _search_news

    with patch("duckduckgo_search.DDGS", side_effect=RuntimeError("network down")):
        result = _search_news("Some Vendor", 5)

    assert result == []


def test_max_results_bounds_are_enforced():
    import pytest as pt
    with pt.raises(Exception):
        VendorNewsInput(vendor_name="Test", max_results=0)
    with pt.raises(Exception):
        VendorNewsInput(vendor_name="Test", max_results=11)
