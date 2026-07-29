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

Edit `.env` with your MySQL credentials. Production uses database **`crypto_signals`** (separate from LeadPilot).

On the GCP VM, create the database once (reuses user `leadpilot`):

```bash
sudo mysql < deploy/init-database.sql
```

The app also attempts `CREATE DATABASE IF NOT EXISTS` on startup when the MySQL user is allowed to.

### GitHub Actions secrets (GCP deploy)

| Secret | Example value |
|--------|----------------|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `leadpilot` |
| `MYSQL_PASSWORD` | *(your MySQL password)* |
| `MYSQL_DATABASE` | `crypto_signals` |
| `SECRET_KEY` | *(long random string)* |

Existing secrets: `GCP_SSH_HOST`, `GCP_SSH_USER`, `GCP_SSH_PRIVATE_KEY`.

## Run

```bash
python run.py
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Step 4 includes

- Historical OHLCV downloader (7–365 days) into `historical_candles`
- Backtest engine with simulated long/short trades from strategy signals
- Full performance metrics (win rate, profit factor, drawdown, streaks, etc.)
- Plotly charts: candlesticks with buy/sell markers, equity curve, drawdown
- `/backtest/` run UI, report page, JSON export, side-by-side comparison

## Step 3 includes

- Visual strategy builder at `/strategies/` (BUY/SELL rules, AND/OR/NOT, per-rule NOT invert)
- Rule types: indicator compare, MACD cross, Bollinger band touch
- Save, edit, delete, clone, enable/disable, import/export JSON
- Assign strategies to coins; scanner runs only assigned pairs (fallback: all enabled coins)
- Preview on live BTC/USDT candles before saving

## Step 2 includes

- Binance OHLCV via CCXT, stored in `historical_candles`
- Indicator engine (EMA, SMA, RSI, MACD, BB, ATR, and more)
- JSON strategy evaluator with seeded **EMA + RSI + MACD** strategy (BTC/USDT, 1H)
- Background APScheduler scanner (`ENABLE_SCHEDULER=true`)
- BUY/SELL signals with duplicate prevention per candle
- SMTP alert emails + test email button
- `/scanner/` dashboard and `/signals/` history

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
