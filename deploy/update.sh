#!/usr/bin/env bash
# Pull the latest code and rebuild the production stack in place. Data volumes are kept.
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
sudo docker image prune -f >/dev/null
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
