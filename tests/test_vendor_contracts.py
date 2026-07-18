from unittest.mock import patch, MagicMock
from tools.vendor_contracts import VendorContractsInput, vendor_list_contracts


def _mock_supabase(vendors, total=None):
    client = MagicMock()
    result = MagicMock()
    result.data = vendors
    result.count = total if total is not None else len(vendors)
    query = client.table.return_value.select.return_value
    query.eq.return_value = query
    query.ilike.return_value = query
    query.gte.return_value = query
    query.order.return_value.range.return_value.execute.return_value = result
    return client


async def test_lists_vendors_as_markdown_table(sample_vendor):
    with patch("utils.supabase_client.get_supabase_client", return_value=_mock_supabase([sample_vendor])):
        result = await vendor_list_contracts(VendorContractsInput())

    assert "DataBridge Ltd" in result
    assert "| # | Vendor |" in result


async def test_invalid_risk_category_is_rejected():
    result = await vendor_list_contracts(VendorContractsInput(risk_category="Nonsense"))
    assert "Invalid risk_category" in result


async def test_empty_results_returns_friendly_message():
    with patch("utils.supabase_client.get_supabase_client", return_value=_mock_supabase([], total=0)):
        result = await vendor_list_contracts(VendorContractsInput(country="Atlantis"))

    assert "No vendors found" in result
    assert "Atlantis" in result


async def test_pagination_hint_appears_when_more_results_exist(sample_vendor):
    with patch("utils.supabase_client.get_supabase_client", return_value=_mock_supabase([sample_vendor], total=25)):
        result = await vendor_list_contracts(VendorContractsInput(limit=1, offset=0))

    assert "more vendor(s) available" in result
    assert "offset=1" in result


def test_limit_bounds_are_enforced():
    import pytest as pt
    with pt.raises(Exception):
        VendorContractsInput(limit=0)
    with pt.raises(Exception):
        VendorContractsInput(limit=51)
