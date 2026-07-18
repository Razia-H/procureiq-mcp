from unittest.mock import patch, MagicMock
from tools.vendor_profile import VendorGetProfileInput, vendor_get_profile


def _mock_supabase(vendor_row):
    """Build a mock Supabase client whose select().ilike()...execute() chain
    returns the given row (or no rows if vendor_row is None)."""
    mock_client = MagicMock()
    result = MagicMock()
    result.data = [vendor_row] if vendor_row else []
    mock_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = result
    return mock_client


async def test_returns_markdown_profile_for_known_vendor(sample_vendor):
    with patch("tools.vendor_profile.get_supabase", return_value=_mock_supabase(sample_vendor)):
        result = await vendor_get_profile(VendorGetProfileInput(vendor_name="DataBridge Ltd"))

    assert "DataBridge Ltd" in result
    assert "72/100" in result
    assert "HIGH RISK" in result


async def test_risk_level_boundaries(low_risk_vendor):
    with patch("tools.vendor_profile.get_supabase", return_value=_mock_supabase(low_risk_vendor)):
        result = await vendor_get_profile(VendorGetProfileInput(vendor_name="SafeSupply Inc"))

    assert "LOW RISK" in result


async def test_returns_json_when_requested(sample_vendor):
    import json
    with patch("tools.vendor_profile.get_supabase", return_value=_mock_supabase(sample_vendor)):
        result = await vendor_get_profile(
            VendorGetProfileInput(vendor_name="DataBridge Ltd", response_format="json")
        )

    parsed = json.loads(result)
    assert parsed["name"] == "DataBridge Ltd"


async def test_vendor_not_found_returns_friendly_message():
    with patch("tools.vendor_profile.get_supabase", return_value=_mock_supabase(None)):
        result = await vendor_get_profile(VendorGetProfileInput(vendor_name="NoSuchVendor"))

    assert "No vendor found" in result
    assert "vendor_search_similar" in result


def test_rejects_empty_vendor_name():
    import pytest as pt
    with pt.raises(Exception):
        VendorGetProfileInput(vendor_name="")


def test_rejects_unknown_fields():
    """extra='forbid' should reject typos/unexpected fields at the input boundary."""
    import pytest as pt
    with pt.raises(Exception):
        VendorGetProfileInput(vendor_name="DataBridge Ltd", format="markdown")
