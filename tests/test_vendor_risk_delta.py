from unittest.mock import patch
from tools.vendor_risk_delta import (
    VendorRiskDeltaInput,
    vendor_analyze_risk_delta,
    _node_build_report,
)


def _fake_final_state(**overrides):
    state = {
        "vendor_name": "DataBridge Ltd",
        "baseline_profile": {"name": "DataBridge Ltd", "country": "India", "category": "Data Services"},
        "news_articles": [{"title": "test"}],
        "news_summary": "Risk appears to be increasing.",
        "baseline_risk_score": 72,
        "current_risk_signal": "Increased",
        "delta_score": 10,
        "drift_drivers": ["New regulatory inquiry"],
        "recommended_actions": ["Escalate to compliance team"],
        "final_report": "",
    }
    state.update(overrides)
    return state


async def test_markdown_report_uses_pipeline_output():
    fake_state = _fake_final_state()
    fake_state = _node_build_report(fake_state)  # builds final_report from the fake state

    with patch("tools.vendor_risk_delta._run_langgraph_pipeline", return_value=fake_state):
        result = await vendor_analyze_risk_delta(VendorRiskDeltaInput(vendor_name="DataBridge Ltd"))

    assert "DataBridge Ltd" in result
    assert "Increased" in result
    assert "Escalate to compliance team" in result


async def test_json_report_computes_projected_score_and_clamps_to_100():
    import json
    fake_state = _fake_final_state(baseline_risk_score=95, delta_score=20)

    with patch("tools.vendor_risk_delta._run_langgraph_pipeline", return_value=fake_state):
        result = await vendor_analyze_risk_delta(
            VendorRiskDeltaInput(vendor_name="DataBridge Ltd", response_format="json")
        )

    parsed = json.loads(result)
    assert parsed["projected_score"] == 100  # 95 + 20 clamped to 100, not 115


def test_build_report_shows_correct_signal_emoji():
    state = _fake_final_state(current_risk_signal="Decreased", delta_score=-15)
    result_state = _node_build_report(state)

    assert "🟢" in result_state["final_report"]
    assert "-15 pts" in result_state["final_report"]
