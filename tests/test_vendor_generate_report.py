import json
from unittest.mock import patch
from tools.vendor_generate_report import VendorGenerateReportInput, vendor_generate_report


async def test_full_report_combines_all_three_sections(sample_vendor):
    with patch("tools.vendor_generate_report._get_vendor", return_value=sample_vendor), \
         patch("tools.vendor_generate_report._search_news", return_value=[{"title": "x"}]), \
         patch("tools.vendor_generate_report._summarise_with_groq", return_value="News signal: stable."), \
         patch("tools.vendor_generate_report._run_rag_compliance_check", return_value="Compliance: needs review."):

        result = await vendor_generate_report(VendorGenerateReportInput(vendor_name="DataBridge Ltd"))

    assert "Executive Risk Report: DataBridge Ltd" in result
    assert "HIGH RISK" in result
    assert "News signal: stable." in result
    assert "Compliance: needs review." in result


async def test_sections_can_be_toggled_off(sample_vendor):
    with patch("tools.vendor_generate_report._get_vendor", return_value=sample_vendor):
        result = await vendor_generate_report(
            VendorGenerateReportInput(
                vendor_name="DataBridge Ltd",
                include_news=False,
                include_regulatory=False,
            )
        )

    assert "Recent Signal (News)" not in result
    assert "Regulatory Compliance" not in result
    assert "Executive Risk Report" in result


async def test_json_output_is_valid_and_complete(sample_vendor):
    with patch("tools.vendor_generate_report._get_vendor", return_value=sample_vendor), \
         patch("tools.vendor_generate_report._search_news", return_value=[]), \
         patch("tools.vendor_generate_report._run_rag_compliance_check", return_value="Compliant."):

        result = await vendor_generate_report(
            VendorGenerateReportInput(vendor_name="DataBridge Ltd", response_format="json")
        )

    parsed = json.loads(result)
    assert parsed["risk_level"] == "HIGH"
    assert parsed["regulatory_summary"] == "Compliant."
    assert "No recent news found" in parsed["news_summary"]


async def test_vendor_not_found_does_not_call_news_or_regulatory():
    """If the vendor lookup fails, we should fail fast rather than
    wasting a Groq/news call on a vendor that doesn't exist."""
    with patch("tools.vendor_generate_report._get_vendor", return_value=None), \
         patch("tools.vendor_generate_report._search_news") as mock_news, \
         patch("tools.vendor_generate_report._run_rag_compliance_check") as mock_reg:

        result = await vendor_generate_report(VendorGenerateReportInput(vendor_name="Ghost Corp"))

    assert "not found" in result.lower()
    mock_news.assert_not_called()
    mock_reg.assert_not_called()


def test_risk_level_boundaries_match_other_tools():
    """risk_level thresholds should stay consistent with vendor_get_profile's
    own thresholds (70+ HIGH, 40-69 MEDIUM, <40 LOW)."""
    from tools.vendor_generate_report import _risk_level

    assert _risk_level(70) == "HIGH"
    assert _risk_level(69) == "MEDIUM"
    assert _risk_level(40) == "MEDIUM"
    assert _risk_level(39) == "LOW"
