import json
import os

from app.exchanges.registry import list_supported_exchanges, normalize_exchange_id
from app.indicators import list_indicator_names
from app.services.config_backup_service import ConfigBackupService
from app.utils.cache import TTLCache


def test_ttl_cache_expires():
    cache: TTLCache[str] = TTLCache(default_ttl_seconds=0.05)
    cache.set("k", "v")
    assert cache.get("k") == "v"
    import time

    time.sleep(0.06)
    assert cache.get("k") is None


def test_exchange_registry():
    assert normalize_exchange_id("Binance") == "binance"
    ids = {e["id"] for e in list_supported_exchanges()}
    assert "binance" in ids


def test_indicator_catalog():
    names = list_indicator_names()
    assert "RSI" in names
    assert "EMA" in names


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "db_ready" in data


def test_api_requires_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-key")
    # New app instance picks up env — recreate client via app fixture limitation:
    # test client uses existing app; api reads os.getenv per request
    bad = client.get("/api/v1/coins", headers={})
    assert bad.status_code == 401
    ok = client.get("/api/v1/coins", headers={"X-API-Key": "secret-test-key"})
    assert ok.status_code == 200


def test_config_backup_roundtrip(app):
    with app.app_context():
        service = ConfigBackupService()
        raw = service.export_json()
        payload = json.loads(raw)
        assert payload["version"] == 1
        assert "strategies" in payload
        stats = service.import_json(raw)
        assert stats["settings"] >= 0


def test_error_pages(client):
    assert client.get("/no-such-page").status_code == 404
    assert b"404" in client.get("/no-such-page").data


def test_settings_backup_page(client):
    response = client.get("/settings/backup")
    assert response.status_code == 200
    assert b"Configuration backup" in response.data
