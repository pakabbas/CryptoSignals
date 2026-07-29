from app.config.settings import MySQLConfig


def test_sqlalchemy_uri_encodes_special_characters_in_password():
    cfg = MySQLConfig(
        host="localhost",
        port=3306,
        user="leadpilot",
        password="LeadPilot@GCP2026",
        database="crypto_signals",
    )
    uri = cfg.sqlalchemy_uri
    assert "LeadPilot%40GCP2026" in uri
    assert uri.endswith("@localhost:3306/crypto_signals?charset=utf8mb4")
