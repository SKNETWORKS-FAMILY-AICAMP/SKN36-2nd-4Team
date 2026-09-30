from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary_uses_committed_cohort_snapshot() -> None:
    response = client.get("/api/v1/summary")
    body = response.json()
    assert response.status_code == 200
    assert body["kpis"]["total_users"] == 9879
    assert body["kpis"]["model_eligible_users"] == 2381
    assert body["model_status"] == "ready"
    assert body["collection_scope"] == "전체 수집 사용자 9,879명"


def test_risk_users_returns_cohort_dashboard_data() -> None:
    response = client.get("/api/v1/risk-users")
    body = response.json()
    assert response.status_code == 200
    assert body["demo"] is False
    assert body["total"] == 2381
    assert len(body["items"]) > 0
    assert body["overview"]["high_risk_users"] > 0


def test_user_detail_returns_committed_user_timeline() -> None:
    candidate = client.get("/api/v1/risk-users", params={"size": 1}).json()["items"][0]
    response = client.get(f"/api/v1/users/{candidate['record_id']}")
    body = response.json()
    assert response.status_code == 200
    assert body["player_id"] == candidate["player_id"]
    assert len(body["performance"]) > 0


def test_user_search_finds_player_id_in_committed_snapshot() -> None:
    candidate = client.get("/api/v1/risk-users", params={"size": 1}).json()["items"][0]
    response = client.get("/api/v1/users/search", params={"q": candidate["player_id"]})
    assert response.status_code == 200
    assert response.json()[0]["player_id"] == candidate["player_id"]


def test_survival_demo_csv_is_resolved_from_repository_root() -> None:
    response = client.get("/api/v1/survival/synthetic-users")
    assert response.status_code == 200
    body = response.json()
    assert body["demo"] is True
    assert body["test_users"] > 0
    assert body["items"]


def test_model_metrics_returns_committed_experiment_snapshot() -> None:
    response = client.get("/api/v1/model/metrics")
    body = response.json()
    assert response.status_code == 200
    assert body["model_status"] == "ready"
    assert body["model_version"] == "core-reselected-2026-08-01"
    assert body["details"]["nested_selection_oof"]["all_core"]["users"] == 2381
    assert body["details"]["nested_selection_oof"]["all_core"]["churners"] == 363
    assert body["metrics"]["pr_auc_ap"] > 0
