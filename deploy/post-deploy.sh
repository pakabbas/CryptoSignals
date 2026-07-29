#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/cryptosignals"
SERVICE_NAME="cryptosignals"
APP_USER="${SUDO_USER:-$(whoami)}"

cd "$APP_DIR"

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "WARNING: $APP_DIR/.env not found. Copy .env.example and set MySQL credentials on the server."
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

sudo nginx -t
sudo systemctl reload nginx

echo "Post-deploy complete: ${SERVICE_NAME} restarted"
