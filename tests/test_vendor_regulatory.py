from unittest.mock import patch, MagicMock
from tools.vendor_regulatory import VendorRegulatoryInput, vendor_check_regulatory


async def test_returns_compliance_analysis(sample_vendor):
    with patch("tools.vendor_regulatory._get_vendor_from_supabase", return_value=sample_vendor), \
         patch("tools.vendor_regulatory._run_rag_compliance_check", return_value="Needs review: GDPR gap."):

        result = await vendor_check_regulatory(
            VendorRegulatoryInput(vendor_name="DataBridge Ltd", regulation="GDPR")
        )

    assert "DataBridge Ltd" in result
    assert "GDPR" in result
    assert "Needs review: GDPR gap." in result


async def test_vendor_not_found_returns_friendly_message():
    with patch("tools.vendor_regulatory._get_vendor_from_supabase", return_value=None):
        result = await vendor_check_regulatory(VendorRegulatoryInput(vendor_name="NoSuchVendor"))

    assert "not found" in result.lower()
    assert "vendor_search_similar" in result


async def test_json_format(sample_vendor):
    import json
    with patch("tools.vendor_regulatory._get_vendor_from_supabase", return_value=sample_vendor), \
         patch("tools.vendor_regulatory._run_rag_compliance_check", return_value="Compliant."):

        result = await vendor_check_regulatory(
            VendorRegulatoryInput(vendor_name="DataBridge Ltd", response_format="json")
        )

    parsed = json.loads(result)
    assert parsed["vendor_name"] == "DataBridge Ltd"
    assert parsed["compliance_analysis"] == "Compliant."


def test_get_vendor_from_supabase_uses_the_correct_client_function(sample_vendor):
    """
    Regression test: this helper imports get_supabase_client from
    utils.supabase_client. That name previously didn't exist there
    (only get_supabase did), so every call silently failed and this
    tool always reported vendors as not found. Confirms the import
    now resolves and the function actually returns data.
    """
    mock_client = MagicMock()
    result = MagicMock()
    result.data = [sample_vendor]
    mock_client.table.return_value.select.return_value.ilike.return_value.execute.return_value = result

    with patch("utils.supabase_client.get_supabase_client", return_value=mock_client):
        from tools.vendor_regulatory import _get_vendor_from_supabase
        vendor = _get_vendor_from_supabase("DataBridge Ltd")

    assert vendor == sample_vendor
