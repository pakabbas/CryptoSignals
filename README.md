# Crypto Signal Bot

Python Flask application for crypto signal monitoring. **Step 1** delivers foundation infrastructure; trading pair focus is **BTC/USDT**.

## Requirements

- Python 3.12+
- MySQL (local XAMPP or GCP)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your MySQL credentials. The app creates the `crypto_signals` database and tables on first run.

## Run

```bash
python run.py
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Step 1 includes

- Flask project structure with services and SQLAlchemy models
- MySQL persistence (coins, settings, SMTP, logs, and placeholder tables for later steps)
- Bootstrap dashboard, BTC/USDT coin page, general & SMTP settings, logs viewer
- Rotating file logs plus DB log entries
- APScheduler heartbeat (scanner wiring in Step 2)

## Project layout

```
app/
  config/          Configuration loader (.env)
  database/        SQLAlchemy + MySQL bootstrap
  models/          ORM models
  routes/          Flask blueprints
  services/        Business logic
  templates/       Bootstrap UI
  static/          CSS/JS
logs/              Runtime log files
run.py             Entry point
```
