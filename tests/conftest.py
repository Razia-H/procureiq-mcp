"""
Shared fixtures for the ProcureIQ test suite.

None of these tests hit real external services (Supabase, Groq, Pinecone,
DuckDuckGo). Everything is mocked so the suite runs fast, offline, and
without needing real API keys.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def fake_env(monkeypatch):
    """Ensure no test accidentally depends on real credentials."""
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("PINECONE_API_KEY", "fake-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "vendor-profiles-test")


@pytest.fixture
def sample_vendor():
    """A representative vendor record shaped like a real Supabase row."""
    return {
        "name": "DataBridge Ltd",
        "risk_score": 72,
        "risk_category": "High",
        "country": "India",
        "category": "Data Services",
        "contract_value": 95000,
        "last_assessment_date": "2026-04-10",
        "last_assessment": "2026-04-10",
        "status": "Under Review",
        "risk_factors": "GDPR compliance gap identified",
        "notes": "Flagged during Q1 review",
    }


@pytest.fixture
def low_risk_vendor():
    """A low-risk vendor, used to test risk-level boundary logic."""
    return {
        "name": "SafeSupply Inc",
        "risk_score": 15,
        "risk_category": "Low",
        "country": "USA",
        "category": "Logistics",
        "contract_value": 20000,
        "last_assessment_date": "2026-06-01",
        "last_assessment": "2026-06-01",
        "status": "Active",
        "risk_factors": "",
        "notes": "",
    }


@pytest.fixture
def sample_news_articles():
    return [
        {
            "title": "DataBridge Ltd faces GDPR inquiry",
            "date": "2026-07-01",
            "source": "TechRisk Daily",
            "url": "https://example.com/article1",
            "body": "Regulators opened an inquiry into DataBridge Ltd's data handling practices.",
        },
        {
            "title": "DataBridge Ltd announces new CISO",
            "date": "2026-06-15",
            "source": "Enterprise Wire",
            "url": "https://example.com/article2",
            "body": "The company appointed a new Chief Information Security Officer.",
        },
    ]
