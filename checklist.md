# Checklist.md

## Instructions for Cursor AI

Review the entire project and verify that every feature from `requirements.md` has been implemented correctly.

For each item below, mark it as:

- ✅ Complete
- ⚠️ Partially Complete
- ❌ Missing

If anything is missing or partially complete:
- Explain why
- Mention the affected file(s)
- Fix it where possible

---

## Core Features

- Flask application runs without errors
- MySQL database is configured and working
- Background scanner works correctly
- Binance market data integration works
- Historical candle download works
- All configured indicators are implemented
- Strategy Builder works
- Buy/Sell signal generation works
- Email (SMTP) alerts work
- Backtesting works correctly
- Charts display correctly
- Settings page works
- Coin management works
- Strategy management works
- Logging works

---

## Code Quality

- No TODOs or unfinished code
- No duplicate code
- Proper error handling
- Clean project structure
- Modular architecture
- No hardcoded secrets
- Configuration loaded from settings/environment

---

## Extra Checks

- Scanner does not generate duplicate alerts
- Signals are generated only after candle close
- API calls are efficient (no unnecessary requests)
- Database queries are efficient
- UI is responsive and user-friendly

---

## Final Review

Perform a complete audit of the project.

If you find bugs, missing features, bad architecture, performance issues, or anything that can be improved—even if it wasn't explicitly mentioned in `requirements.md`—implement the improvements and explain what was changed.