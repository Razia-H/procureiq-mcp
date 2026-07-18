from unittest.mock import patch, MagicMock, AsyncMock
from tools.vendor_search import VendorSearchInput, vendor_search_similar


def _mock_pinecone_index(matches):
    index = MagicMock()
    results = MagicMock()
    results.matches = matches
    index.query.return_value = results
    return index


def _mock_supabase_lookup(vendor_row):
    client = MagicMock()
    result = MagicMock()
    result.data = [vendor_row] if vendor_row else []
    client.table.return_value.select.return_value.ilike.return_value.execute.return_value = result
    return client


def _make_match(vendor_name, score):
    match = MagicMock()
    match.metadata = {"vendor_name": vendor_name}
    match.score = score
    return match


async def test_returns_enriched_results(sample_vendor):
    matches = [_make_match("DataBridge Ltd", 0.93)]

    # Note: vendor_search.py does its imports *inside* the function body,
    # so we patch at the source modules, not tools.vendor_search.
    with patch("utils.embeddings.get_embedding", new=AsyncMock(return_value=[0.1, 0.2, 0.3])), \
         patch("utils.pinecone_client.get_pinecone_index", return_value=_mock_pinecone_index(matches)), \
         patch("utils.supabase_client.get_supabase_client", return_value=_mock_supabase_lookup(sample_vendor)):

        result = await vendor_search_similar(VendorSearchInput(query="risky data vendors in India"))

    assert "DataBridge Ltd" in result
    assert "0.93" in result


async def test_no_matches_returns_friendly_message():
    with patch("utils.embeddings.get_embedding", new=AsyncMock(return_value=[0.1, 0.2, 0.3])), \
         patch("utils.pinecone_client.get_pinecone_index", return_value=_mock_pinecone_index([])):

        result = await vendor_search_similar(VendorSearchInput(query="nonexistent industry xyz"))

    assert "No similar vendors found" in result


def test_get_embedding_exists_and_is_awaitable():
    """
    Regression test: utils.embeddings previously had no get_embedding
    function at all (only the plural get_embeddings() and a sync
    embed_text()). vendor_search_similar imports and awaits get_embedding
    specifically — its absence broke this tool silently. This test fails
    loudly if that name ever goes missing again.
    """
    import inspect
    from utils import embeddings

    assert hasattr(embeddings, "get_embedding")
    assert inspect.iscoroutinefunction(embeddings.get_embedding)


def test_top_k_bounds_are_enforced():
    import pytest as pt
    with pt.raises(Exception):
        VendorSearchInput(query="test", top_k=0)
    with pt.raises(Exception):
        VendorSearchInput(query="test", top_k=21)
