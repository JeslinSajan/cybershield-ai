#!/usr/bin/env bash
# ==============================================================================
# CyberShield AI Agent — Linux systemd Service Installer
# ==============================================================================
set -euo pipefail

INSTALL_DIR="/opt/cybershield-agent"
SERVICE_USER="cybershield"
SERVICE_GROUP="cybershield"
SERVICE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

echo "=========================================================="
echo "  CyberShield AI Agent Service Installation"
echo "=========================================================="

# 1. Require root / sudo
if [[ $EUID -ne 0 ]]; then
    echo "[-] Error: This installation script must be run as root (or with sudo)." >&2
    exit 1
fi

# 2. Create system user and group if they don't already exist
if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
    echo "[+] Creating system group: $SERVICE_GROUP"
    groupadd --system "$SERVICE_GROUP"
fi

if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    echo "[+] Creating system user: $SERVICE_USER"
    useradd --system --gid "$SERVICE_GROUP" --no-create-home \
        --shell /usr/sbin/nologin --comment "CyberShield Agent Daemon" "$SERVICE_USER"
fi

# 3. Create target directory
echo "[+] Preparing directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 4. Copy agent files
echo "[+] Copying agent files to $INSTALL_DIR..."
cp -r "$SERVICE_SRC"/* "$INSTALL_DIR/"

# 5. Set up Python virtual environment if missing
if [[ ! -d "$INSTALL_DIR/venv" ]]; then
    echo "[+] Creating Python virtual environment in $INSTALL_DIR/venv..."
    python3 -m venv "$INSTALL_DIR/venv"
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
        "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    fi
fi

# 6. Secure file ownership and permissions
echo "[+] Setting file permissions..."
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"

if [[ -f "$INSTALL_DIR/.env" ]]; then
    chmod 600 "$INSTALL_DIR/.env"
fi

if [[ -f "$INSTALL_DIR/agent_identity.json" ]]; then
    chmod 600 "$INSTALL_DIR/agent_identity.json"
fi

# 7. Install and enable systemd unit
echo "[+] Installing systemd unit file..."
cp "$INSTALL_DIR/cybershield-agent.service" "$SYSTEMD_DIR/cybershield-agent.service"
chmod 644 "$SYSTEMD_DIR/cybershield-agent.service"

echo "[+] Reloading systemd daemon..."
systemctl daemon-reload

echo "[+] Enabling cybershield-agent service on boot..."
systemctl enable cybershield-agent.service

echo ""
echo "=========================================================="
echo "  Installation Successful!"
echo "=========================================================="
echo "Commands to manage the service:"
echo "  - Start service:   sudo systemctl start cybershield-agent"
echo "  - Stop service:    sudo systemctl stop cybershield-agent"
echo "  - Check status:    sudo systemctl status cybershield-agent"
echo "  - View live logs:  sudo journalctl -u cybershield-agent -f"
echo "=========================================================="
