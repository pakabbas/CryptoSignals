def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"BTC/USDT" in response.data


def test_primary_coin_seeded(client):
    response = client.get("/coins/")
    assert response.status_code == 200
    assert b"BTC/USDT" in response.data


def test_scanner_page_loads(client):
    response = client.get("/scanner/")
    assert response.status_code == 200
    assert b"Live scanner" in response.data


def test_signals_page_loads(client):
    response = client.get("/signals/")
    assert response.status_code == 200
    assert b"Signal history" in response.data


def test_settings_hub_and_smtp(client):
    response = client.get("/settings/")
    assert response.status_code == 200
    assert b"Email alerts" in response.data

    response = client.get("/settings/smtp")
    assert response.status_code == 200
    assert b"Receiver email" in response.data
