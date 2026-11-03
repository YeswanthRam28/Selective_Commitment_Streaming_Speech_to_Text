#!/usr/bin/env bash
set -e

# Detect current working directory and user
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_USER="${SUDO_USER:-$(whoami)}"

echo "=========================================================="
echo "Installing TWO 26 Services for systemd"
echo "Repo root : ${REPO_DIR}"
echo "Run user  : ${CURRENT_USER}"
echo "=========================================================="

# Create systemd unit files with resolved absolute paths
sed -e "s|/opt/two26|${REPO_DIR}|g" \
    -e "s|%USER%|${CURRENT_USER}|g" \
    "${REPO_DIR}/services/two26-backend.service" | sudo tee /etc/systemd/system/two26-backend.service > /dev/null

sed -e "s|/opt/two26|${REPO_DIR}|g" \
    -e "s|%USER%|${CURRENT_USER}|g" \
    "${REPO_DIR}/services/two26-frontend.service" | sudo tee /etc/systemd/system/two26-frontend.service > /dev/null

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling services..."
sudo systemctl enable two26-backend.service
sudo systemctl enable two26-frontend.service

echo "Starting services..."
sudo systemctl restart two26-backend.service
sudo systemctl restart two26-frontend.service

echo ""
echo "Services status:"
sudo systemctl status two26-backend.service --no-pager
sudo systemctl status two26-frontend.service --no-pager

echo ""
echo "TWO 26 Services successfully installed and running!"

