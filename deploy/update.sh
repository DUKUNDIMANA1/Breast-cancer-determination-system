#!/bin/bash
# =============================================================
# BreastCare AI — Update script
# Run on VPS to pull latest code and restart: bash update.sh
# =============================================================

APP_DIR="/var/www/breastcare"
APP_NAME="breastcare"

echo "Pulling latest code..."
cd $APP_DIR
sudo -u breastcare git pull origin main

echo "Installing new dependencies..."
sudo -u breastcare $APP_DIR/venv/bin/pip install -r requirements.txt --quiet

echo "Restarting service..."
systemctl restart $APP_NAME

echo "Done! Status:"
systemctl status $APP_NAME --no-pager
