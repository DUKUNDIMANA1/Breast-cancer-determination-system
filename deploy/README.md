# BreastCare AI — VPS Deployment Guide

Stack: **Ubuntu 22.04 + Python 3.11 + Gunicorn + Nginx + Let's Encrypt SSL**

---

## Prerequisites

- A VPS running Ubuntu 20.04 or 22.04 (DigitalOcean, Hetzner, Linode, AWS EC2)
- Root or sudo access
- Your MongoDB Atlas URI
- A domain name (optional but recommended for SSL)
- The `cnn_model.h5` file (upload separately — too large for GitHub)

---

## Step 1 — Connect to your VPS

```bash
ssh root@YOUR_VPS_IP
```

---

## Step 2 — Clone the repository

```bash
mkdir -p /var/www/breastcare
git clone https://github.com/DUKUNDIMANA1/Breast-cancer-determination-system.git /var/www/breastcare
cd /var/www/breastcare
```

---

## Step 3 — Run the setup script

```bash
bash deploy/setup.sh
```

This will:
- Install Python, Nginx, system dependencies
- Create a virtual environment and install packages
- Create the `.env` file template
- Register and start the systemd service

---

## Step 4 — Configure environment variables

```bash
nano /var/www/breastcare/.env
```

Fill in your real values:

```env
SECRET_KEY=generate_a_64_char_random_string_here
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/breastcare_ai
MONGO_DB_NAME=breastcare_ai
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 5 — Upload the CNN model

The `cnn_model.h5` file is too large for GitHub. Upload it manually:

```bash
# From your Windows machine (in PowerShell):
scp "C:\path\to\artifacts\cnn_model.h5" root@YOUR_VPS_IP:/var/www/breastcare/artifacts/
```

Then set permissions on the VPS:
```bash
chown breastcare:breastcare /var/www/breastcare/artifacts/cnn_model.h5
```

---

## Step 6 — Configure Nginx

```bash
# Copy config
cp /var/www/breastcare/deploy/nginx.conf /etc/nginx/sites-available/breastcare

# Edit it — replace YOUR_DOMAIN_OR_IP
nano /etc/nginx/sites-available/breastcare

# Enable it
ln -s /etc/nginx/sites-available/breastcare /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t && systemctl reload nginx
```

---

## Step 7 — SSL Certificate (Free, Let's Encrypt)

Only do this if you have a domain pointing to your VPS:

```bash
bash /var/www/breastcare/deploy/ssl_setup.sh yourdomain.com
```

---

## Step 8 — Verify everything works

```bash
# Check service is running
systemctl status breastcare

# Check logs
journalctl -u breastcare -f

# Check Nginx
systemctl status nginx
```

Open your browser: `http://YOUR_VPS_IP` or `https://yourdomain.com`

---

## Updating the system

Whenever you push new code to GitHub, on the VPS run:

```bash
bash /var/www/breastcare/deploy/update.sh
```

---

## Useful Commands

| Command | Purpose |
|---|---|
| `systemctl restart breastcare` | Restart the app |
| `systemctl stop breastcare` | Stop the app |
| `journalctl -u breastcare -f` | Live logs |
| `systemctl reload nginx` | Reload Nginx config |
| `nginx -t` | Test Nginx config syntax |
| `certbot renew` | Renew SSL certificate |

---

## Recommended VPS Specs

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB | 40 GB |
| OS | Ubuntu 20.04 | Ubuntu 22.04 |

> **Note:** The CNN model (TensorFlow) needs at least 2GB RAM to load.
> If RAM is tight, use a swap file: `fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`

---

## Providers

| Provider | Cheapest Plan | Link |
|---|---|---|
| Hetzner | €4/mo (CX22, 2 vCPU, 4GB RAM) | hetzner.com |
| DigitalOcean | $12/mo (2 vCPU, 2GB RAM) | digitalocean.com |
| Linode (Akamai) | $12/mo (1 vCPU, 2GB RAM) | linode.com |
| AWS EC2 | Free tier (t2.micro, 1GB RAM) | aws.amazon.com |
