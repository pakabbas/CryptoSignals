#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/cryptosignals"
NGINX_AVAIL="/etc/nginx/sites-available/cryptosignals"
NGINX_ENABLED="/etc/nginx/sites-enabled/cryptosignals"
DOMAIN="cryptosignals.btkdeals.com"

sudo mkdir -p "$APP_DIR"
sudo chown -R muhamad_abbas:www-data "$APP_DIR"
sudo chmod -R 775 "$APP_DIR"

if [[ ! -f "$NGINX_AVAIL" ]]; then
  sudo cp /tmp/cryptosignals-nginx.conf "$NGINX_AVAIL"
  sudo ln -sfn "$NGINX_AVAIL" "$NGINX_ENABLED"
  sudo nginx -t
  sudo systemctl reload nginx
fi

if [[ ! -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    --register-unsafely-without-email --redirect || true
else
  sudo nginx -t
  sudo systemctl reload nginx
fi

echo "Remote setup complete for $DOMAIN"
