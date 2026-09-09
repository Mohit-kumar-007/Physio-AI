#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu 24.04 EC2 instance to run PhysioMind.
#
#   curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/deploy/setup-ec2.sh | bash
# or, having already cloned:
#   bash deploy/setup-ec2.sh
#
# Safe to re-run.

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/physiomind}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

[[ $EUID -eq 0 ]] && die "Run as the ubuntu user, not root. Docker is added to your group instead."

say "Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl git
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
         -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
         docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker "$USER"
    NEEDS_RELOGIN=1
else
    echo "Docker already installed."
fi

# A t3.micro has 1 GB of RAM. Building the image and analysing a long session
# can both spike; swap turns an out-of-memory kill into a slow moment.
say "Ensuring 2 GB of swap"
if ! sudo swapon --show | grep -q /swapfile; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile >/dev/null
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
    echo "2 GB swap enabled."
else
    echo "Swap already present."
fi

say "Enabling automatic security updates"
sudo apt-get install -y -qq unattended-upgrades >/dev/null
sudo dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true

if [[ ! -d "$REPO_DIR" ]]; then
    say "Clone your repository to $REPO_DIR, then re-run this script"
    echo "    git clone <your-repo-url> $REPO_DIR"
    exit 0
fi

cd "$REPO_DIR"

say "Creating .env"
if [[ -f .env ]]; then
    echo ".env already exists - leaving it alone."
else
    read -rp "Domain pointed at this instance (e.g. physio.example.com): " DOMAIN
    read -rp "Email for certificate expiry notices: " EMAIL
    [[ -z "$DOMAIN" || -z "$EMAIL" ]] && die "Both values are required."

    cat > .env <<EOF
DOMAIN=$DOMAIN
EMAIL=$EMAIL
PHYSIO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
PHYSIO_JWT_EXPIRE_HOURS=168
EOF
    chmod 600 .env
    echo "Wrote .env with a freshly generated secret key."
fi

if [[ "${NEEDS_RELOGIN:-0}" == "1" ]]; then
    say "Log out and back in, then run: cd $REPO_DIR && docker compose up -d --build"
    echo "(Your user was just added to the docker group; the shell needs to reload it.)"
    exit 0
fi

say "Building and starting"
docker compose up -d --build

say "Done"
DOMAIN_VALUE=$(grep '^DOMAIN=' .env | cut -d= -f2-)
echo "The site should be live at: https://$DOMAIN_VALUE"
echo
echo "Certificates take up to a minute on first boot. Watch progress with:"
echo "    docker compose logs -f caddy"
