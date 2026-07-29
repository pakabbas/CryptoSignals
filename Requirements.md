```md
# Crypto Signal Bot
## Requirements Document (requirements.md)

# Project Overview

Build a Python-based Crypto Signal Bot capable of:

- Monitoring one or more cryptocurrency trading pairs (BTC/USDT, ETH/USDT, etc.)
- Checking technical indicators continuously in the background
- Detecting Buy and Sell (Short) opportunities
- Sending email alerts via configurable SMTP
- Providing a modern web interface for configuration
- Allowing users to create custom strategies by combining indicators
- Backtesting strategies against historical market data
- Displaying detailed statistics and charts

This is NOT an auto-trading bot.

The system only generates signals and sends alerts.

Future versions may support exchange integration.

---

# Technology Stack

Backend
- Python 3.12+
- Flask
- SQLAlchemy
- APScheduler
- Pandas
- NumPy
- TA-Lib (preferred) or pandas-ta
- ccxt
- Plotly
- Jinja2

Database
- MySQL (primary — already available on GCP)
- SQLAlchemy with PyMySQL / mysqlclient driver

Frontend
- HTML
- Bootstrap 5
- JavaScript
- Chart.js
- Plotly

Email
- SMTP

Charts
- Plotly
- TradingView Lightweight Charts (optional)

Deployment
- Windows (local / XAMPP)
- Linux
- Google Cloud Platform (GCP) — MySQL already installed
- Docker (future)

---

# Main Features

## Live Scanner

Continuously monitor selected coins.

Example:

BTC/USDT

ETH/USDT

SOL/USDT

DOGE/USDT

etc.

Scanner interval should be configurable.

Example

Every minute

Every candle close

Every 5 minutes

---

## Supported Timeframes

1m

5m

15m

30m

1H

4H

1D

---

## Supported Exchanges

Initially

Binance

Future

Bybit

OKX

KuCoin

Coinbase

---

# Indicators

The system must support adding indicators independently.

Initial indicators

Trend

- EMA
- SMA
- Supertrend
- VWAP

Momentum

- RSI
- MACD
- Stochastic RSI
- CCI

Volatility

- Bollinger Bands
- ATR
- Keltner Channel

Volume

- Volume MA
- OBV
- MFI

Breakout

- Donchian Channel

Support for adding more indicators later without changing the core architecture.

---

# Strategy Builder

User should be able to visually build strategies.

Example

BUY IF

EMA50 > EMA200

AND

MACD Crosses Up

AND

RSI > 55

AND

Volume > SMA20

THEN

Signal Buy

Another example

Price touches lower Bollinger Band

AND

RSI < 30

THEN

Signal Buy

Support

AND

OR

NOT

Multiple conditions

Nested conditions (future)

---

# Signal Engine

Generate

BUY

SELL (Short)

No Signal

Signal must only trigger after candle close.

Prevent duplicate alerts on the same candle.

---

# Email Alerts

SMTP configurable.

Settings

SMTP Server

Port

Username

Password

SSL/TLS

Sender Email

Receiver Email

Subject template

Email example

--------------------------------

BUY Signal

Coin:
BTCUSDT

Timeframe:
1H

Price:
117540

Strategy:
EMA + RSI + MACD

Time:
2026-08-01 14:00 UTC

--------------------------------

Support test email.

---

# Historical Data

Download OHLCV candles.

Store locally.

Allow

7 Days

30 Days

90 Days

180 Days

365 Days

Future

Auto cache.

---

# Backtesting Engine

Run strategy against historical candles.

Calculate

Total Trades

Winning Trades

Losing Trades

Win Rate

Profit %

Loss %

Profit Factor

Average Win

Average Loss

Maximum Drawdown

Largest Win

Largest Loss

Longest Winning Streak

Longest Losing Streak

Buy Signals

Sell Signals

Average Trade Duration

Return %

---

# Charts

Display

Candlestick chart

Indicators

Entry points

Exit points

Buy markers

Sell markers

Equity curve

Drawdown chart

---

# Dashboard

Display

Scanner Status

Running Strategies

Coins being monitored

Last Signals

Recent Alerts

Last Scan Time

CPU Usage (future)

Memory Usage (future)

---

# Settings

General

Timezone

Exchange

API Keys (future)

Scanner Interval

Default Timeframe

SMTP

Database

Theme

---

# Coin Management

User can

Add Coin

Remove Coin

Enable

Disable

Search

Group coins

---

# Strategy Management

Create

Edit

Delete

Clone

Export JSON

Import JSON

Enable

Disable

---

# Logging

Application log

Scanner log

Strategy log

Email log

Errors

Warnings

Debug mode

---

# Database

Engine: MySQL

Connection configured via environment / settings (host, port, database name, user, password).

Use SQLAlchemy ORM; connection string example:

mysql+pymysql://user:password@host:3306/crypto_signals

Create a dedicated database (e.g. `crypto_signals`) on the existing GCP MySQL instance.

## Database Tables

coins

strategies

indicator_settings

signals

backtest_results

smtp_settings

app_settings

logs

historical_candles

---

# Project Structure

crypto_signal_bot/

app/

config/

database/

services/

scanner/

strategies/

indicators/

backtester/

charts/

templates/

static/

models/

routes/

utils/

logs/

tests/

requirements.txt

run.py

README.md

---

# Coding Standards

Use OOP.

Use type hints.

Use dataclasses where appropriate.

Keep modules independent.

Avoid duplicated code.

Each feature should be reusable.

Use dependency injection where appropriate.

Functions should be small and focused.

---

# Future Features

Telegram notifications

Discord notifications

Slack notifications

Push notifications

Webhook support

AI strategy optimisation

Machine Learning signal scoring

Exchange auto trading

Paper trading

Portfolio tracking

Risk management

Position sizing

Stop Loss

Take Profit

Trailing Stop

Multi-user support

Authentication

Dark mode

Docker deployment

REST API

---

# Development Roadmap

---

# STEP 1 — Foundation & Infrastructure

Goal:
Create the project's backbone.

Tasks

- Initialise Flask project
- Configure project structure
- MySQL database setup (connect to existing GCP MySQL)
- SQLAlchemy models (MySQL-compatible types)
- Settings management
- Logging system
- Basic Bootstrap UI
- Dashboard skeleton
- Coin management
- SMTP settings page
- Configuration loader
- Background scheduler setup (APScheduler)
- Application configuration system
- Base service architecture

Deliverable

A fully running web application with persistent settings, database support, logging, scheduler infrastructure, and clean project architecture.

---

# STEP 2 — Live Scanner & Signal Engine

Goal:
Implement market monitoring and signal generation.

Tasks

- Connect to Binance using CCXT
- Fetch OHLCV data
- Store historical candles
- Create indicator calculation engine
- Implement supported indicators
- Strategy evaluation engine
- Continuous background scanner
- Candle-close detection
- Signal generation
- Duplicate signal prevention
- Email notifications
- Scanner dashboard
- Signal history page

Deliverable

A working application capable of monitoring configured markets, evaluating strategies, generating Buy/Sell signals, and sending email alerts.

---

# STEP 3 — Strategy Builder & Configuration

Goal:
Allow users to build strategies without coding.

Tasks

- Visual strategy builder UI
- AND/OR condition support
- Indicator parameter editor
- Strategy validation
- Save/Edit/Delete strategies
- Clone strategies
- Enable/Disable strategies
- Import/Export strategy JSON
- Assign strategies to selected coins
- Configure timeframe per strategy
- Strategy preview

Deliverable

A flexible strategy builder enabling users to create, manage, and apply custom indicator-based trading strategies.

---

# STEP 4 — Backtesting & Analytics

Goal:
Evaluate strategies using historical market data.

Tasks

- Historical data downloader
- Backtesting engine
- Simulated trade execution
- Performance calculations
- Win/loss statistics
- Drawdown analysis
- Profit factor calculation
- Equity curve generation
- Candlestick chart visualisation
- Entry/Exit markers
- Strategy comparison
- Export backtest results
- Performance reports

Deliverable

A complete backtesting module with detailed analytics, visualisations, and historical strategy evaluation.

---

# STEP 5 — Optimisation, Polish & Future Readiness

Goal:
Refine the application for reliability, scalability, and future expansion.

Tasks

- Performance optimisation
- Caching
- Improved error handling
- Unit tests
- Integration tests
- UI polishing
- Responsive layout
- Configuration backup/restore
- Advanced logging
- Docker support
- REST API foundation
- Plugin-ready indicator architecture
- Multi-exchange abstraction
- Documentation
- Deployment guide
- Security review
- Code refactoring

Deliverable

A production-ready crypto signal platform with a modular architecture, comprehensive documentation, strong testing coverage, and a clear foundation for future enhancements such as auto-trading, Telegram notifications, and AI-assisted strategy optimisation.
```
