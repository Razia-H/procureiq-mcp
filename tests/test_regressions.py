"""
Regression tests for bugs found while building this test suite.

Both bugs shared the same shape: a tool file imported a function name
from a utils module that had never been defined there. Because every
tool wraps its logic in a broad try/except, the resulting ImportError
was silently swallowed and surfaced only as a generic "not found" or
"error" message — with no stack trace, no log line pointing at the
real cause. These tests exist so that if either name is ever renamed
or removed again, the suite fails loudly instead of degrading silently.
"""

import inspect


def test_get_supabase_client_exists():
    """
    Bug: vendor_search, vendor_regulatory, vendor_contracts, and
    vendor_risk_delta all import get_supabase_client from
    utils.supabase_client, but only get_supabase() was defined there.
    4 of the original 6 tools were broken from day one as a result.
    """
    from utils import supabase_client

    assert hasattr(supabase_client, "get_supabase_client")
    assert callable(supabase_client.get_supabase_client)


def test_get_embedding_exists_and_is_async():
    """
    Bug: vendor_search.py imports and awaits get_embedding from
    utils.embeddings, but only get_embeddings() (plural) and a
    synchronous embed_text() existed. vendor_search_similar was
    broken from day one as a result.
    """
    from utils import embeddings

    assert hasattr(embeddings, "get_embedding")
    assert inspect.iscoroutinefunction(embeddings.get_embedding)


def test_all_tool_modules_import_cleanly():
    """
    Broad safety net: every tool module should import without raising,
    given fake-but-present environment variables. This is what would
    have caught both bugs above immediately, without needing to know
    the specific broken function names in advance.
    """
    import importlib

    tool_modules = [
        "tools.vendor_profile",
        "tools.vendor_search",
        "tools.vendor_news",
        "tools.vendor_regulatory",
        "tools.vendor_contracts",
        "tools.vendor_risk_delta",
        "tools.vendor_generate_report",
    ]

    for module_name in tool_modules:
        importlib.import_module(module_name)  # raises on failure, which is the test
