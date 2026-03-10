from __future__ import annotations


def test_health_and_version(client) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["success"] is True
    assert health_payload["data"]["status"] == "ok"

    version = client.get("/version")
    assert version.status_code == 200
    version_payload = version.json()
    assert version_payload["success"] is True
    assert "app_version" in version_payload["data"]
