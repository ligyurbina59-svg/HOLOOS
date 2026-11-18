from fastapi.testclient import TestClient

from android24creator_backend.main import app

client = TestClient(app)


def test_studio_status_lists_scope_and_safety():
    response = client.get("/api/studio/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IMPLEMENTADO"
    assert body["safety"]["generated_code_execution"] is False
    assert body["features"]["value_investing_calculator"] == "IMPLEMENTADO"


def test_product_plan_returns_platforms_and_human_review():
    response = client.post("/api/studio/plan", json={
        "product_name": "MN24 Demo",
        "description": "A prototype to create small business apps from prompts.",
        "target_users": "Independent developers and small businesses",
        "platforms": ["web", "android", "pwa"],
        "budget_usd": 100,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["product_specification"]["platforms"] == ["web", "android", "pwa"]
    assert body["vibe_coding"]["human_review_required"] is True
    assert body["lovable_inspired_builder"]["code_generation"] == "PENDING"


def test_product_plan_rejects_budget_over_100():
    response = client.post("/api/studio/plan", json={
        "product_name": "MN24 Demo",
        "description": "A prototype to create small business apps from prompts.",
        "target_users": "Developers",
        "platforms": ["web"],
        "budget_usd": 150,
    })
    assert response.status_code == 422


def test_finance_dcf_calculates_positive_npv():
    response = client.post("/api/studio/finance/evaluate", json={
        "initial_investment": 100,
        "annual_cash_flows": [40, 50, 60],
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.02,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "simplified_dcf_scenario"
    assert body["illustrative_intrinsic_value"] > 0
    assert body["npv"] > 0
    assert "not investment advice" in body["warning"]


def test_finance_rejects_growth_not_below_discount():
    response = client.post("/api/studio/finance/evaluate", json={
        "initial_investment": 100,
        "annual_cash_flows": [40, 50],
        "discount_rate": 0.05,
        "terminal_growth_rate": 0.05,
    })
    assert response.status_code == 422


def test_qa_checklist_does_not_claim_tests_ran():
    response = client.get("/api/studio/qa/checklist")
    assert response.status_code == 200
    assert response.json()["pipeline_status"] == "PENDIENTE"
