#!/bin/bash
# =============================================================
# BreastCare AI — VPS Setup Script (Ubuntu 20.04 / 22.04)
# Run once as root: bash setup.sh
# =============================================================

set -e

APP_NAME="breastcare"
APP_USER="breastcare"
APP_DIR="/var/www/breastcare"
PYTHON_VERSION="3.11"

echo "======================================================"
echo "  BreastCare AI — VPS Setup"
echo "======================================================"

# ── 1. System update ─────────────────────────────────────
echo "[1/8] Updating system..."
apt-get update -y && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv nginx git curl wget \
  build-essential libssl-dev libffi-dev python3-dev \
  libopencv-dev libglib2.0-0 libsm6 libxext6 libxrender-dev

# ── 2. Create app user ───────────────────────────────────
echo "[2/8] Creating app user: $APP_USER"
if ! id "$APP_USER" &>/dev/null; then
  useradd --system --shell /bin/bash --home $APP_DIR --create-home $APP_USER
fi

# ── 3. Clone / copy app ──────────────────────────────────
echo "[3/8] Setting up app directory: $APP_DIR"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

echo ""
echo "  >>> Clone your GitHub repo into $APP_DIR"
echo "  >>> Run: git clone https://github.com/DUKUNDIMANA1/Breast-cancer-determination-system.git $APP_DIR"
echo "  >>> Then re-run this script or continue manually."
echo ""

# ── 4. Python virtual environment ────────────────────────
echo "[4/8] Creating Python virtual environment..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# ── 5. Create .env file ──────────────────────────────────
echo "[5/8] Creating .env file..."
if [ ! -f "$APP_DIR/.env" ]; then
  cat > $APP_DIR/.env << 'EOF'
# BreastCare AI — Production Environment Variables
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_64_CHARS

# MongoDB Atlas URI — replace with your actual URI
MONGO_URI=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/breastcare_ai?retryWrites=true&w=majority
MONGO_DB_NAME=breastcare_ai

# Email (optional — for password reset)
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your_app_password

# Render flag (set to False for VPS)
RENDER=False
EOF
  chown $APP_USER:$APP_USER $APP_DIR/.env
  chmod 600 $APP_DIR/.env
  echo "  >>> IMPORTANT: Edit $APP_DIR/.env with your real values!"
fi

# ── 6. Create uploads/reports dirs ──────────────────────
echo "[6/8] Creating upload directories..."
mkdir -p $APP_DIR/static/uploads $APP_DIR/static/reports $APP_DIR/artifacts
touch $APP_DIR/static/uploads/.gitkeep
chown -R $APP_USER:$APP_USER $APP_DIR/static $APP_DIR/artifacts

# ── 7. Systemd service ───────────────────────────────────
echo "[7/8] Creating systemd service..."
cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=BreastCare AI — Gunicorn
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 2 \\
    --worker-class sync \\
    --timeout 120 \\
    --bind unix:$APP_DIR/breastcare.sock \\
    --access-logfile $APP_DIR/logs/access.log \\
    --error-logfile $APP_DIR/logs/error.log \\
    app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

mkdir -p $APP_DIR/logs
chown -R $APP_USER:$APP_USER $APP_DIR/logs

systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME

echo "[8/8] Setup complete!"
echo ""
echo "  Service status: systemctl status $APP_NAME"
echo "  View logs:      journalctl -u $APP_NAME -f"
echo "  Restart:        systemctl restart $APP_NAME"
echo ""
echo "  Next: Configure Nginx (see nginx.conf) and SSL (see ssl_setup.sh)"
