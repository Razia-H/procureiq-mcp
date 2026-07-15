import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_supabase():
    global _client
    if _client is None:
        _client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    return _client


def get_supabase_client():
    """
    Alias for get_supabase().

    4 of 6 tools (vendor_search, vendor_regulatory, vendor_contracts,
    vendor_risk_delta) import this name specifically. Without it those
    tools raise ImportError on every call, which is silently swallowed
    by their try/except blocks and surfaces as a false "vendor not found"
    instead of a real error. This alias fixes that without touching the
    four call sites.
    """
    return get_supabase()
