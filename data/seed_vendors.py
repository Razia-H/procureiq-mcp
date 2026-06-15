import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.supabase_client import get_supabase
from dotenv import load_dotenv

load_dotenv()

vendors = [
    {
        "name": "TechCorp Solutions",
        "category": "Software",
        "country": "United States",
        "contract_value": 250000,
        "risk_score": 25,
        "status": "active",
        "last_assessment_date": "2026-03-15",
        "risk_factors": "Minor data handling concerns flagged in 2025 audit. Resolved.",
        "notes": "Long-standing vendor since 2019. Strong compliance track record."
    },
    {
        "name": "GlobalLogix",
        "category": "Logistics",
        "country": "Germany",
        "contract_value": 180000,
        "risk_score": 45,
        "status": "active",
        "last_assessment_date": "2026-01-20",
        "risk_factors": "Late delivery incidents Q3 2025. Financial instability reported in Q4 2025.",
        "notes": "Under review. Quarterly check-ins scheduled."
    },
    {
        "name": "SecureVault Inc",
        "category": "Cybersecurity",
        "country": "United Kingdom",
        "contract_value": 320000,
        "risk_score": 15,
        "status": "active",
        "last_assessment_date": "2026-05-01",
        "risk_factors": "None identified.",
        "notes": "Top-rated vendor. ISO 27001 certified. Preferred supplier."
    },
    {
        "name": "DataBridge Ltd",
        "category": "Data Services",
        "country": "India",
        "contract_value": 95000,
        "risk_score": 72,
        "status": "under_review",
        "last_assessment_date": "2026-04-10",
        "risk_factors": "GDPR compliance gap identified. Data breach incident March 2026. Regulatory fine pending.",
        "notes": "Escalated to legal team. Contract renewal on hold."
    },
    {
        "name": "CloudNine Systems",
        "category": "Cloud Infrastructure",
        "country": "United States",
        "contract_value": 410000,
        "risk_score": 38,
        "status": "active",
        "last_assessment_date": "2026-02-28",
        "risk_factors": "Single point of failure in EU data center. Mitigation plan submitted.",
        "notes": "High contract value. Priority monitoring enabled."
    },
    {
        "name": "SupplyChain Pro",
        "category": "Supply Chain",
        "country": "China",
        "contract_value": 760000,
        "risk_score": 81,
        "status": "high_risk",
        "last_assessment_date": "2026-05-20",
        "risk_factors": "Geopolitical exposure. Export control regulations under review. Two compliance violations in 2025.",
        "notes": "Board-level escalation required. Alternative vendors being evaluated."
    },
    {
        "name": "Meridian Consulting",
        "category": "Professional Services",
        "country": "Canada",
        "contract_value": 140000,
        "risk_score": 20,
        "status": "active",
        "last_assessment_date": "2026-04-05",
        "risk_factors": "None identified.",
        "notes": "Excellent performance scores. Contract renewal recommended."
    },
    {
        "name": "FastPay Fintech",
        "category": "Financial Services",
        "country": "Singapore",
        "contract_value": 220000,
        "risk_score": 63,
        "status": "under_review",
        "last_assessment_date": "2026-03-30",
        "risk_factors": "PCI DSS audit findings. Payment processing irregularities detected Q1 2026.",
        "notes": "Finance team monitoring closely. Remediation deadline June 2026."
    }
]

def seed_vendors():
    supabase = get_supabase()
    print("Seeding vendors table...")
    for vendor in vendors:
        result = supabase.table("vendors").upsert(vendor, on_conflict="name").execute()
        print(f"   Inserted: {vendor['name']} — Risk Score: {vendor['risk_score']}")
    print(f"\nDone. {len(vendors)} vendors seeded successfully.")

if __name__ == "__main__":
    seed_vendors()
