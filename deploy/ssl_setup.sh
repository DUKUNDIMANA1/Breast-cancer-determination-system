#!/bin/bash
# =============================================================
# BreastCare AI — Free SSL with Let's Encrypt (Certbot)
# Run AFTER nginx.conf is set up and domain is pointed to VPS
# Usage: bash ssl_setup.sh yourdomain.com
# =============================================================

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
  echo "Usage: bash ssl_setup.sh yourdomain.com"
  exit 1
fi

echo "Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

echo "Obtaining SSL certificate for $DOMAIN..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN

echo "Enabling HTTPS in Nginx config..."
# Certbot auto-modifies nginx config — just reload
systemctl reload nginx

echo ""
echo "SSL setup complete!"
echo "  Certificate: /etc/letsencrypt/live/$DOMAIN/"
echo "  Auto-renewal: certbot renew --dry-run"
echo ""
echo "  Update nginx.conf: uncomment the HTTPS server block"
echo "  and set server_name to: $DOMAIN"
