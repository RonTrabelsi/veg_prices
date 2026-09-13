#!/usr/bin/env bash
# One-time setup of an Oracle Cloud "Always Free" Ubuntu ARM VM for veg_prices.
# Run as the default "ubuntu" user:  bash setup-oracle-vm.sh
#
# Installs Docker and Tailscale, tunes the kernel for Elasticsearch, clones the repository and starts the
# production stack. The app is reachable only through your Tailscale network (http://<vm-name>:3000).
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/RonTrabelsi/veg_prices.git}"
APP_DIR="${APP_DIR:-$HOME/veg_prices}"

echo "==> System packages"
sudo apt-get update -q
sudo apt-get install -y -q ca-certificates curl git

echo "==> Kernel setting Elasticsearch requires (vm.max_map_count)"
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-elasticsearch.conf >/dev/null
sudo sysctl -q --system

echo "==> Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker

echo "==> Tailscale (private access, no public ports)"
if ! command -v tailscale >/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
# Oracle's Ubuntu images ship an iptables INPUT chain that rejects everything but SSH.
# Allow traffic arriving over the Tailscale interface, persistently.
if ! sudo iptables -C INPUT -i tailscale0 -j ACCEPT 2>/dev/null; then
  sudo iptables -I INPUT 1 -i tailscale0 -j ACCEPT
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q netfilter-persistent iptables-persistent
  sudo netfilter-persistent save
fi

echo "==> Application"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
git pull --ff-only
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

cat <<MSG

Done. Two things left, both interactive:

  1. Join this VM to your Tailscale network (prints a login link):
       sudo tailscale up --hostname veg-prices

  2. Wait a few minutes for the first data load, then from any device on your Tailscale network open:
       http://veg-prices:3000

Useful commands (from $APP_DIR):
  sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f periodic_scraper
  sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
  bash deploy/update.sh        # pull the latest code and rebuild
MSG
