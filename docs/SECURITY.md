# Security notes

## Secrets

- Never commit `.env`, SMTP passwords, or MySQL credentials.
- Use GitHub Actions secrets for production deploy.
- Rotate Gmail app passwords if exposed; update `SMTP_PASSWORD` secret and DB via Settings or `deploy/apply_smtp_env.py`.

## Application

- Set a strong `SECRET_KEY` in production.
- Optional `API_KEY` locks `/api/v1/*` when set; leave unset only on trusted networks.
- MySQL user should have least privilege on `crypto_signals` only.
- Gunicorn binds to localhost; nginx terminates TLS — keep firewall rules tight.

## Data & email

- Signal emails contain market data, not account keys (no exchange trading keys in this app).
- Configuration backup exports SMTP settings **without** password; re-enter on import.

## Operations

- Review `logs/` and **Logs** UI for scanner/email errors.
- Keep dependencies updated: `pip install -U -r requirements.txt` and redeploy.
- Run `pytest` before releases.

## Future hardening (not all implemented)

- CSRF on forms (Flask-WTF)
- Rate limiting on API and login-less admin UI
- HTTPS HSTS at nginx (recommended for production domain)
