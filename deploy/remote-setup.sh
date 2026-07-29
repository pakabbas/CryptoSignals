#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/cryptosignals"
NGINX_AVAIL="/etc/nginx/sites-available/cryptosignals"
NGINX_ENABLED="/etc/nginx/sites-enabled/cryptosignals"
DOMAIN="cryptosignals.btkdeals.com"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"

sudo mkdir -p "$APP_DIR/public"
sudo chown -R muhamad_abbas:www-data "$APP_DIR"
sudo chmod -R 775 "$APP_DIR"

if [[ -f "$CERT_DIR/fullchain.pem" ]]; then
  sudo cp /tmp/cryptosignals-nginx.conf "$NGINX_AVAIL"
else
  sudo cp /tmp/cryptosignals-nginx-http.conf "$NGINX_AVAIL"
fi

sudo ln -sfn "$NGINX_AVAIL" "$NGINX_ENABLED"

if [[ ! -f "$CERT_DIR/fullchain.pem" ]]; then
  sudo nginx -t
  sudo systemctl reload nginx
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    --register-unsafely-without-email --redirect || true
  if [[ -f "$CERT_DIR/fullchain.pem" ]]; then
    sudo cp /tmp/cryptosignals-nginx.conf "$NGINX_AVAIL"
  fi
fi

sudo nginx -t
sudo systemctl reload nginx

if [[ -f "$APP_DIR/deploy/post-deploy.sh" ]]; then
  bash "$APP_DIR/deploy/post-deploy.sh"
else
  bash /tmp/cryptosignals-post-deploy.sh
fi

echo "Remote setup complete for $DOMAIN"
