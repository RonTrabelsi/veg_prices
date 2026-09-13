# Deploying on Oracle Cloud "Always Free"

Runs the whole stack 24/7 for free, reachable only from your own devices through Tailscale. No public ports.

**What you get:** an ARM VM (up to 4 cores / 24 GB RAM, permanently free), Docker running the same
`docker-compose.yml` as on your laptop plus [`docker-compose.prod.yml`](../docker-compose.prod.yml), and the app at
`http://veg-prices:3000` on any phone or laptop signed into your Tailscale account.

## 1. Oracle account (once, ~10 minutes)
1. https://www.oracle.com/cloud/free/ → **Start for free**. A credit card is required for identity verification;
   Always Free resources are never charged. Pick the home region closest to Israel (e.g. *Israel Central (Jerusalem)*
   or *Germany Central (Frankfurt)*) — it cannot be changed later, and the free ARM shape must have capacity there.
2. After sign-up you land in the console. Wait for the "account is being provisioned" banner to clear.

## 2. Create the VM (~5 minutes)
1. Console menu → **Compute → Instances → Create instance**.
2. **Name:** `veg-prices`.
3. **Image and shape → Edit:**
   - Image: **Canonical Ubuntu 24.04** (the aarch64 build is chosen automatically with the shape below).
   - Shape: **Ampere → VM.Standard.A1.Flex**, set **4 OCPUs** and **24 GB** memory (the Always Free maximum).
4. **Networking:** keep the default new VCN with a public subnet, **Assign a public IPv4 address: yes**
   (needed only for SSH during setup; the app itself is not exposed).
5. **Add SSH keys:** upload your public key (`cat ~/.ssh/id_ed25519.pub` on your Mac; create one with
   `ssh-keygen -t ed25519` if you have none).
6. **Boot volume:** 50 GB default is enough (Always Free allows 200 GB total).
7. **Create.** If you get *Out of capacity for shape VM.Standard.A1.Flex*: try again in a few hours, try a
   different availability domain in the same region, or reduce to 2 OCPUs / 12 GB (still plenty).

Do **not** open any ingress ports in the subnet's security list besides the default SSH (22). Access is via Tailscale.

## 3. Set up the VM (~10 minutes, mostly waiting)
From your Mac, with the public IP shown on the instance page:
```bash
ssh ubuntu@<PUBLIC_IP>
```
On the VM:
```bash
curl -fsSL https://raw.githubusercontent.com/RonTrabelsi/veg_prices/main/deploy/setup-oracle-vm.sh -o setup.sh
bash setup.sh
```
The script installs Docker and Tailscale, sets `vm.max_map_count` for Elasticsearch, opens the firewall for the
Tailscale interface only, clones the repository and starts the production stack (first build ~5 minutes).

Then join the VM to your Tailscale network — it prints a login link, open it in your browser:
```bash
sudo tailscale up --hostname veg-prices
```

## 4. Your devices
1. Install Tailscale on your Mac and on your father's phone: https://tailscale.com/download.
2. Sign in with the same account (or invite your father as a user; the personal plan includes 3 users).
3. Open **http://veg-prices:3000**. If the name does not resolve, enable *MagicDNS* in the Tailscale admin
   console (https://login.tailscale.com/admin/dns) or use the VM's Tailscale IP from `tailscale ip -4`.

The first data load (prices for every configured vegetable, 20 years of weather, the holidays calendar) takes a few
minutes; the periodic scraper logs show progress:
```bash
cd ~/veg_prices && sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f periodic_scraper
```

## Day to day
- **Update to the latest code:** `bash ~/veg_prices/deploy/update.sh` (data is kept).
- **Kibana** is off by default to save memory. To run it: add `--profile kibana` to the compose command, and reach
  it with an SSH tunnel: `ssh -L 5601:localhost:5601 ubuntu@<PUBLIC_IP>` → http://localhost:5601 (it has no
  published port even then; the tunnel needs `ports` for kibana in a local override, or use
  `docker compose exec`). Simplest: keep using Kibana on your laptop against your local copy.
- **Reboots** are handled: Docker starts on boot and every service has `restart: unless-stopped`.
- **Oracle reclaims idle Always Free instances** (CPU under 20% for 7 days, among other signals). This stack
  scrapes daily and Elasticsearch idles low, so watch for Oracle's warning e-mail; the usual remedy is to upgrade the
  account to *Pay As You Go* — Always Free resources remain free, you just need a card on file with billing enabled.

## Security notes
- Nothing but SSH is reachable from the internet. Elasticsearch, Kibana and the write API have no authentication
  and are not published at all in production; the web app is published on 3000 but blocked by Oracle's security
  list and reachable only over Tailscale.
- Anyone in your Tailscale network can load vegetables (the ＋ button). That's you and your father.
- SSH is key-only by default on Oracle images. Once Tailscale works you can also SSH over it
  (`ssh ubuntu@veg-prices`) and remove the public IP entirely.
