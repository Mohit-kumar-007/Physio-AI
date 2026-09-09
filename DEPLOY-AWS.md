# Deploying PhysioMind to AWS EC2

Step by step, from nothing to a live HTTPS site.

**Time:** ~30 minutes. **Cost:** free tier, plus a domain name (~₹800/year) if
you do not already own one.

---

## Before you start

You need **a domain name**. This is not optional decoration:

> Browsers only allow camera access on HTTPS, and an `ec2-….amazonaws.com`
> hostname **cannot** be issued a TLS certificate. Without a domain there is no
> certificate, without a certificate there is no camera, and without the camera
> this app does nothing.

Any of these work:

- A real domain from Namecheap, GoDaddy, Cloudflare, BigRock (~₹800/year)
- A **free** subdomain from [DuckDNS](https://duckdns.org) — Let's Encrypt
  issues certificates for these, so it is a genuine option, not a workaround

---

## Step 1 — Launch the instance

1. Sign in to the [AWS Console](https://console.aws.amazon.com) → **EC2** →
   **Launch instance**.
2. Fill in:

   | Field | Value |
   |---|---|
   | Name | `physiomind` |
   | AMI | **Ubuntu Server 24.04 LTS** |
   | Instance type | **t3.micro** (look for "Free tier eligible") |
   | Key pair | **Create new** → name it `physiomind-key` → downloads a `.pem` |
   | Storage | **20 GiB** gp3 (free tier allows 30 GiB) |

3. Under **Network settings** → **Edit**, add these inbound rules:

   | Type | Port | Source | Why |
   |---|---|---|---|
   | SSH | 22 | **My IP** | Your admin access. Never `0.0.0.0/0`. |
   | HTTP | 80 | Anywhere `0.0.0.0/0` | Certificate issuance + HTTPS redirect |
   | HTTPS | 443 | Anywhere `0.0.0.0/0` | The actual site |

4. **Launch instance.**

> Pick a region close to your users. `ap-south-1` (Mumbai) for India.

---

## Step 2 — Give it a fixed address

A stopped instance loses its public IP, which would break your DNS record.

**EC2 → Elastic IPs → Allocate Elastic IP** → **Actions → Associate** → select
your instance.

Note the address, e.g. `13.201.45.67`.

> Keep it associated. An Elastic IP is free *while attached to a running
> instance* and billed hourly when idle.

---

## Step 3 — Point your domain at it

In your registrar's DNS settings, add:

| Type | Name | Value |
|---|---|---|
| A | `physio` (or `@` for the root) | your Elastic IP |

For DuckDNS, just set the IP in their dashboard.

Verify before continuing — certificate issuance fails if DNS has not
propagated:

```bash
nslookup physio.yourdomain.com
```

It must return your Elastic IP. Usually a few minutes; occasionally up to an hour.

---

## Step 4 — Connect

```bash
chmod 400 physiomind-key.pem
ssh -i physiomind-key.pem ubuntu@YOUR_ELASTIC_IP
```

On Windows PowerShell, `chmod` does not exist — right-click the `.pem` →
Properties → Security → Advanced → disable inheritance, and leave only your own
user with read access. Or use the browser-based **EC2 Instance Connect** from
the console and skip the key entirely.

---

## Step 5 — Push your code to GitHub

From your **local machine**, if you have not already:

```bash
git add -A && git commit -m "chore: add EC2 deployment config" && git push
```

---

## Step 6 — Run the setup script

Back on the **EC2 instance**:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ~/physiomind
bash ~/physiomind/deploy/setup-ec2.sh
```

It installs Docker, adds 2 GB of swap (a 1 GB instance needs it), enables
automatic security updates, and asks for your domain and email to generate
`.env` with a fresh secret key.

It will ask you to log out and back in once, so your user picks up its new
docker group membership:

```bash
exit
ssh -i physiomind-key.pem ubuntu@YOUR_ELASTIC_IP
cd ~/physiomind && docker compose up -d --build
```

The first build takes 3–5 minutes on a t3.micro.

---

## Step 7 — Check it

```bash
docker compose ps                 # both services should be "running"
docker compose logs -f caddy      # watch the certificate being issued
```

Then open **https://physio.yourdomain.com** — you should get a padlock, and
"Start Session" should prompt for camera permission.

If the certificate is still pending, wait a minute and reload. Caddy retries
automatically.

---

## Day-to-day

```bash
cd ~/physiomind

git pull && docker compose up -d --build     # deploy an update
docker compose logs -f app                   # application logs
docker compose restart app                   # restart just the app
docker compose down                          # stop everything
```

### Back up your data

Accounts, sessions and uploaded reports live in the `physio-data` volume.
Nothing else backs it up for you.

```bash
docker run --rm -v physiomind_physio-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/physio-backup-$(date +%F).tar.gz -C /data .
```

Copy that file off the instance — `scp`, or push it to S3. An instance
failure without an off-box copy means the data is gone.

### Restore

```bash
docker compose down
docker run --rm -v physiomind_physio-data:/data -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/physio-backup-YYYY-MM-DD.tar.gz -C /data"
docker compose up -d
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Certificate never issues | DNS not pointing at the instance, or port 80 closed | `nslookup` your domain; check the security group allows 80 from anywhere |
| Camera prompt never appears | Page is on HTTP, or the certificate failed | Confirm the padlock. HTTP cannot access the camera, full stop. |
| `permission denied` on docker | Group membership not reloaded | Log out and back in |
| Build killed partway | Ran out of RAM | The setup script adds swap; confirm with `swapon --show` |
| 502 from Caddy | App container not healthy | `docker compose logs app` |
| Site loads, exercises empty | App cannot reach its database | `docker compose logs app`; check the `physio-data` volume exists |

---

## Costs after the free tier

Free tier is time-limited — 12 months on older accounts, a credit allowance on
newer ones. **Set a billing alarm now** (Billing → Budgets → a $5/month alert)
so a surprise does not arrive as a bill.

After it lapses, roughly:

| Item | Monthly |
|---|---|
| t3.micro (on-demand, ap-south-1) | ~$8 |
| 20 GB gp3 storage | ~$1.60 |
| Data transfer (light use) | ~$0–1 |
| **Total** | **~$10** |

For comparison, Render's managed tier is ~$7 and includes TLS, backups and
deploys. EC2 wins on the free year and on control; it loses on ongoing cost and
on the fact that patching, certificate renewal, backups and monitoring are now
your job.

---

## Before real patients use this

- [ ] Billing alarm set
- [ ] Backups running and **restore tested** — an untested backup is a guess
- [ ] SSH restricted to your IP, not `0.0.0.0/0`
- [ ] Angle thresholds reviewed by a qualified physiotherapist
- [ ] Privacy policy published, and a lawful basis for storing health data.
      Diagnoses and uploaded medical reports are sensitive personal data under
      India's DPDP Act, and GDPR/HIPAA elsewhere.

Do not put real patient data in a demo deployment.
