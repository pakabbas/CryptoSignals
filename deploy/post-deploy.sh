#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/cryptosignals"
SERVICE_NAME="cryptosignals"
APP_USER="${SUDO_USER:-$(whoami)}"

cd "$APP_DIR"

if [[ ! -f "$APP_DIR/.env" ]]; then
  if [[ -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "Created $APP_DIR/.env from .env.example — update MySQL credentials on the server."
  else
    echo "WARNING: $APP_DIR/.env not found."
  fi
fi

if [[ ! -d "$APP_DIR/.venv" ]]; then
  python3 -m venv "$APP_DIR/.venv"
fi

"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

TMP_SERVICE="/tmp/${SERVICE_NAME}.service"
sed "s/APP_USER/${APP_USER}/g" "$APP_DIR/deploy/cryptosignals.service" > "$TMP_SERVICE"
sudo cp "$TMP_SERVICE" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sleep 2

if ! curl -fsSL http://127.0.0.1:5000/health | grep -q CryptoSignals; then
  echo "Gunicorn health check failed. Service status:"
  sudo systemctl status "$SERVICE_NAME" --no-pager || true
  sudo journalctl -u "$SERVICE_NAME" -n 40 --no-pager || true
  exit 1
fi

sudo nginx -t
sudo systemctl reload nginx

echo "Post-deploy complete: ${SERVICE_NAME} restarted"
