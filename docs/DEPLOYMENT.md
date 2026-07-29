# Deployment guide

CryptoSignals is deployed to GCP via GitHub Actions (`.github/workflows/deploy.yml`) and can run locally, on XAMPP MySQL, or with Docker.

## Production (GCP VM)

1. **MySQL** — Create database and user once:
   ```bash
   sudo mysql < deploy/init-database.sql
   ```
2. **GitHub secrets** — `GCP_SSH_*`, `MYSQL_*`, `SECRET_KEY`, optional SMTP secrets, optional `API_KEY`.
3. **Push to `main`** — Workflow rsyncs to `/var/www/cryptosignals`, runs `deploy/post-deploy.sh` (venv, Gunicorn, nginx).
4. **Verify** — `curl https://cryptosignals.btkdeals.com/health` should report `db_ready: true`.

### Server layout

| Path | Purpose |
|------|---------|
| `/var/www/cryptosignals` | Application root |
| `/var/www/cryptosignals/.env` | Environment (not in git) |
| `deploy/cryptosignals.service` | systemd unit template |
| `deploy/post-deploy.sh` | Install deps and restart |

### Manual restart

```bash
sudo systemctl restart cryptosignals
sudo journalctl -u cryptosignals -n 50 --no-pager
```

## Local (XAMPP)

1. Copy `.env.example` to `.env` and set MySQL credentials.
2. `python -m venv .venv` and `pip install -r requirements.txt`.
3. `python run.py` — open http://127.0.0.1:5000/

Set `ENABLE_SCHEDULER=true` for live scanning.

## Docker

```bash
docker compose up --build
```

App: http://localhost:5000/  
MySQL exposed on host port **3307** for debugging.

## Exchange / geo-blocking (GCP US)

Binance and Bybit often return 451/403 from US cloud IPs. Probe from the server:

```bash
.venv/bin/python deploy/probe_exchanges.py
```

Production default is **Kraken** (verified on GCP). **Binance US** also works from the same VM.

## Configuration backup

Use **Settings → Backup & restore** or `GET /settings/backup/download` (authenticated session) to export JSON. Import merges settings and adds strategies; SMTP password must be supplied separately on import.

## REST API

Base path: `/api/v1/`. If `API_KEY` is set in the environment, send header `X-API-Key: <value>`.

Endpoints: `health`, `coins`, `strategies`, `signals`, `backtests`, `indicators`, `exchanges`.

## CI tests

`.github/workflows/test.yml` runs `pytest` on push/PR (SQLite in-memory, no Binance calls in default suite).
