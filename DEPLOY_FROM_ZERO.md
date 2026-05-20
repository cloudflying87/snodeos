# Deploy SnoDeos From Zero

A complete, beginner-friendly guide to launching a copy of this site for your own snowmobile club. **No prior experience required.** If you can copy/paste commands and follow instructions, you can do this.

**Time estimate:** 3–5 hours spread over a day. Most steps are "wait while it installs."

**What you'll end up with:**
- A live club website at your own domain (e.g. `https://snodeos.com`)
- HTTPS automatically (no SSL certs to manage)
- Email sending (via Resend)
- Text messages to members (via Twilio)
- The ability to edit the site from your laptop with help from ChatGPT or Claude

---

## How this works, in plain English

Your site will live on a **VPS** — basically a small computer in a data center that you rent for ~$6/month. The code lives in **GitHub** (think of it as Google Docs for code). You'll edit code on **your laptop** using **VSCode**, push changes to GitHub, then tell the VPS to pull and rebuild.

We'll use four free/cheap services:
- **Cloudflare** — handles your domain name and provides a secure tunnel to your VPS (no firewall ports to open).
- **Tailscale** — a private network so you can SSH into your VPS without exposing it to the internet.
- **Resend** — sends emails (welcome messages, announcements).
- **Twilio** — sends text messages (and receives them, if you want).

```
Your laptop  ──git push──►  GitHub  ──build.sh pulls──►  VPS (Docker containers)
                                                         │
                                                         ▼
                                              Cloudflare Tunnel
                                                         │
                                                         ▼
                                                   Your members
```

---

# Part 1 — Create accounts

Do these in a browser. Keep a password manager open; you'll collect a lot of credentials.

### 1.1 GitHub (free)
1. Go to https://github.com and click **Sign up**.
2. Pick a username (this is public — e.g. `brainerd-snodeos`).
3. Verify your email.

### 1.2 Cloudflare (free)
1. Go to https://cloudflare.com and click **Sign Up**.
2. Verify your email.

### 1.3 A domain name (~$10–15/year)
You need a domain like `yourclub.com`. Two options:
- **Buy through Cloudflare** (recommended — auto-configures DNS): once logged into Cloudflare, click **Domain Registration → Register Domains**.
- **Buy elsewhere** (Namecheap, Google Domains, etc.): you'll later point its nameservers to Cloudflare.

For this guide we'll assume **Cloudflare-registered domain** — easiest.

### 1.4 DigitalOcean (~$6/month — the VPS)
1. Go to https://digitalocean.com and sign up (often includes $200 free credit for first 60 days).
2. Add a payment method.

### 1.5 Resend (free for low volume)
1. Go to https://resend.com and sign up.
2. We'll come back to configure later.

### 1.6 Twilio (pay-as-you-go, ~$1.15/mo for phone number + $0.008/text)
1. Go to https://twilio.com and sign up.
2. Verify your personal phone number when prompted.
3. Skip "buy a number" for now — we'll do that later.

### 1.7 Tailscale (free for up to 100 devices)
1. Go to https://tailscale.com and sign up (use your GitHub account — easiest).

### 1.8 AI coding assistant (optional but recommended)
- **Claude** — https://claude.ai (best for code editing in my experience)
- or **ChatGPT** — https://chatgpt.com

The free tier of either is enough to make small edits.

---

# Part 2 — Set up your laptop

### 2.1 Install VSCode
1. Go to https://code.visualstudio.com and download the installer for your operating system.
2. Run the installer with default options.
3. Open VSCode.

### 2.2 Install Git
Git is the program VSCode uses to talk to GitHub.
- **Windows:** https://git-scm.com/download/win — run the installer, all defaults.
- **Mac:** open Terminal (Cmd+Space, type "Terminal"), then type `git --version` and press Enter. If macOS asks to install developer tools, click **Install**. Done.

### 2.3 Tell Git who you are
Open VSCode. Then open the built-in terminal: **View → Terminal** (or Ctrl+\` / Cmd+\`). Paste these two commands, replacing the values:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Use the *same email* you used for GitHub.

### 2.4 Install Tailscale on your laptop
- Download from https://tailscale.com/download
- Install and log in with the same account from step 1.7.
- After login, your laptop is on your private network.

### 2.5 Set up SSH keys
SSH keys are like a passwordless login for servers. You generate a "key pair" — keep the private one secret, copy the public one to wherever you want to log in.

In the VSCode terminal:

```bash
ssh-keygen -t ed25519 -C "you@example.com"
```

Press **Enter** three times to accept defaults. Then:

```bash
cat ~/.ssh/id_ed25519.pub
```

(On Windows in PowerShell: `Get-Content $HOME\.ssh\id_ed25519.pub`)

Copy the output — it starts with `ssh-ed25519`. You'll paste this into GitHub and into your VPS in later steps.

### 2.6 Add your SSH key to GitHub
1. In GitHub, click your avatar (top right) → **Settings**.
2. Left sidebar → **SSH and GPG keys**.
3. **New SSH key**. Title: "My Laptop". Paste the key from step 2.5. **Add SSH key**.

### 2.7 Install a Claude or ChatGPT extension in VSCode (optional)
- For **Claude Code**, install the official extension: VSCode → Extensions (square icon left sidebar) → search "Claude Code" → Install.
- For **ChatGPT/Copilot**, search "GitHub Copilot" or "Continue".

You can also just keep claude.ai or chatgpt.com open in a browser tab and paste code back and forth — works fine.

---

# Part 3 — Get the code

### 3.1 Fork the repo on GitHub
A "fork" is your own copy of someone else's repo.

1. Go to the source repo on GitHub (the one this code lives in).
2. Click **Fork** (top right).
3. Name it whatever you want, e.g. `yourclub-website`.

### 3.2 Clone the fork to your laptop
"Cloning" downloads the code so you can edit it locally.

In VSCode terminal, navigate to where you want the code (e.g. your Desktop):

```bash
cd ~/Desktop
git clone git@github.com:YOUR-USERNAME/yourclub-website.git
cd yourclub-website
code .
```

The last command (`code .`) opens this folder in VSCode.

---

# Part 4 — Cloudflare DNS

### 4.1 If you bought your domain through Cloudflare
DNS is already set up. Skip to 4.2.

### 4.1b If you bought your domain elsewhere
1. In Cloudflare, click **Add a Site**.
2. Enter your domain. Pick the **Free** plan.
3. Cloudflare shows you two **nameserver** addresses. Go to where you bought the domain (Namecheap, Google Domains, etc.), find DNS settings, and replace the existing nameservers with Cloudflare's two. **This can take up to 24 hours to take effect.** Wait for Cloudflare to email you "your site is active."

### 4.2 Leave DNS records empty for now
We're going to use a **Cloudflare Tunnel** instead of normal DNS records, so don't add any `A` or `CNAME` records yet. We'll do that automatically in Part 7.

---

# Part 5 — Create the VPS

### 5.1 Spin up a Droplet
1. Log into DigitalOcean.
2. Click **Create → Droplets**.
3. **Region:** pick the one closest to your members (e.g. NYC, SFO).
4. **OS:** Ubuntu 24.04 LTS (default).
5. **Size:** Basic → Regular → **$6/mo (1GB RAM, 1 vCPU, 25GB)** — fine for a club site.
6. **Authentication:** SSH key. Click **New SSH Key**, paste the key from step 2.5, give it a name like "My Laptop".
7. **Hostname:** call it whatever you want, e.g. `snodeos-prod`.
8. Click **Create Droplet**. Takes ~30 seconds.

### 5.2 Copy the IP address
Once the Droplet is created, DigitalOcean shows its **public IPv4 address** (something like `134.122.45.67`). Copy it.

### 5.3 First SSH login (just to confirm it works)
In VSCode terminal:

```bash
ssh root@134.122.45.67
```

(Use your actual IP.) The first time you'll see "Are you sure you want to continue connecting?" — type `yes`. You should land on a shell prompt like `root@snodeos-prod:~#`. You're inside the server.

Type `exit` to come back to your laptop.

---

# Part 6 — Secure the VPS with Tailscale

This is where most beginner guides leave a server exposed to the public internet on port 22, which is a hacking magnet. We're going to do better: put the VPS on your Tailscale network so only your devices can SSH to it.

### 6.1 Install Tailscale on the VPS
SSH back in, then run:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

It'll print a URL — **open it in your laptop's browser** and approve. The VPS is now on your Tailscale network and got a Tailscale IP like `100.x.x.x`.

### 6.2 Find the Tailscale IP
On the VPS:

```bash
tailscale ip -4
```

That's the IP you'll use from now on. Write it down.

### 6.3 (Optional but recommended) Block public SSH
Once you've confirmed you can SSH via the Tailscale IP, you can lock down the public IP:

```bash
sudo ufw allow in on tailscale0
sudo ufw allow 80/tcp comment "Cloudflare Tunnel might need this — skip if using tunnel only"
sudo ufw enable
sudo ufw default deny incoming
```

**Test before you exit!** Open a second terminal and confirm SSH via Tailscale IP works, then close the public-IP session.

### 6.4 Add a non-root user (optional, more secure)
Running as root is fine for a single-purpose VPS, but if you want a dedicated user:

```bash
sudo adduser deploy            # answer prompts; remember the password
sudo usermod -aG sudo deploy   # give it sudo
sudo mkdir /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
```

Then from your laptop: `ssh deploy@100.x.x.x` instead of `ssh root@...`.

---

# Part 7 — Install Docker on the VPS

The site runs as Docker containers. Docker handles all the dependencies (Python, Postgres, nginx) so you don't have to.

SSH into the VPS, then:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
exit
```

The `exit` is so the group change takes effect — log back in:

```bash
ssh root@100.x.x.x   # or deploy@100.x.x.x
docker --version     # should print "Docker version 27.x..." or similar
```

If `docker` works without `sudo`, you're set.

---

# Part 8 — Cloudflare Tunnel

A Cloudflare Tunnel makes your VPS reachable at your domain **without opening any ports** on the VPS. Cloudflare's edge connects outbound to the tunnel daemon running on your VPS — magic.

### 8.1 Create the tunnel in Cloudflare
1. In Cloudflare, go to **Zero Trust** (left sidebar — or `one.dash.cloudflare.com`).
2. **Networks → Tunnels → Create a tunnel**.
3. **Cloudflared** as the connector type.
4. Name it `snodeos-tunnel` (or whatever).
5. **Save tunnel**.
6. The next page shows installation commands. **You don't need to run them** — the docker-compose.yml in this repo already runs `cloudflared` for you. Instead, **copy the token** (the long string starting with `eyJ...`) — you'll paste it into `.env` in step 10.
7. Click **Next**.
8. **Public Hostname** tab: add a route:
   - Subdomain: leave empty (or use `www`)
   - Domain: pick your domain
   - Service: `http://nginx:80`  (this is the internal name of the nginx container)
9. **Save tunnel**.

That's it. Cloudflare will automatically create the DNS record for you.

---

# Part 9 — Resend (email)

### 9.1 Verify your domain
1. In Resend, **Domains → Add Domain** → enter your domain.
2. Resend gives you DNS records to add (SPF, DKIM, MX records).
3. In Cloudflare DNS, click **Add record** for each one Resend gave you. Type, name, and value all copy directly from Resend.
4. Back in Resend, click **Verify** — usually instant. (Set the orange cloud to gray for the DKIM/SPF records if Resend asks — these are not proxied.)

### 9.2 Get an API key
1. Resend → **API Keys → Create API Key**.
2. Name: "Snodeos site". Permission: "Sending access".
3. Copy the key (starts with `re_`) — you'll paste it into the site's Communications page later.

---

# Part 10 — Twilio (SMS)

### 10.1 Buy a phone number
1. In Twilio, **Phone Numbers → Buy a Number**.
2. Pick one with **SMS** capability in your area code. ~$1.15/month.
3. Note the number — format like `+12185551234`.

### 10.2 Get credentials
On the Twilio dashboard, find:
- **Account SID** (starts with `AC...`)
- **Auth Token** (click the eye icon to reveal)

You'll paste both into the site's Communications page later.

### 10.3 Wire up two-way texting (optional but recommended)
By default, replies to your texts go nowhere — they sit in Twilio's logs and the sender gets no response. To capture them in the panel:

1. In Twilio, go to **Phone Numbers → Manage → Active Numbers → click your number**.
2. Scroll to **Messaging Configuration**.
3. Set **"A message comes in"**:
   - Webhook: `https://yourclub.com/webhooks/twilio/sms/`
   - HTTP method: `HTTP POST`
4. **Save**.

That's it. Anyone who texts your Twilio number now shows up in **Manage Panel → SMS Inbox**, and the officer notification email gets a heads-up. Twilio signs every webhook so the endpoint rejects spoofed calls.

---

# Part 11 — First deploy

### 11.1 Clone the repo onto the VPS
SSH into the VPS:

```bash
cd ~
git clone https://github.com/YOUR-USERNAME/yourclub-website.git snodeos
cd snodeos
```

(Note: HTTPS clone is fine for read-only on the server. If you ever need to push from the server itself, set up a deploy key — not needed for this workflow.)

### 11.2 Create the `.env` file
```bash
cp .env.example .env
nano .env
```

Edit each line. Press Ctrl+O then Enter to save, Ctrl+X to exit nano. Required values:

| Variable | What to set |
|----------|-------------|
| `SECRET_KEY` | Generate a random string: run `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourclub.com,www.yourclub.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://yourclub.com,https://www.yourclub.com` |
| `SITE_URL` | `https://yourclub.com` |
| `DEFAULT_FROM_EMAIL` | `Your Club <noreply@yourclub.com>` |
| `POSTGRES_USER` | Make one up, e.g. `snodeos_user` |
| `POSTGRES_PASSWORD` | Long random string (use a password manager) |
| `POSTGRES_DB` | `snodeos` |
| `DATABASE_URL` | `postgresql://snodeos_user:THE_PASSWORD@db:5432/snodeos` (matches the three above) |
| `CLOUDFLARE_TUNNEL_TOKEN` | The token you copied in step 8.1 |

Leave email/SMS values blank — we'll configure those in the panel UI.

### 11.3 Run the build
```bash
./build.sh
```

This script does everything:
1. Snapshots the DB (skipped on first run — no DB yet)
2. Pulls latest code from git
3. Rebuilds Docker images
4. Runs database migrations
5. Collects static files
6. Seeds initial data
7. Starts all services

Takes 3–5 minutes the first time. When it says **DEPLOYMENT COMPLETE!**, visit `https://yourclub.com` — your site should load!

### 11.4 Create your admin user
```bash
docker compose exec web python3 manage.py createsuperuser
```

Answer the prompts. Now you can log in at `https://yourclub.com/accounts/login/`.

---

# Part 12 — Configure the site through the UI

Log in as your superuser. Go to **Manage Panel** (top-right menu).

### 12.1 Communications (email + SMS)
1. **Settings → Communications**.
2. Paste your **Resend API key** in the Resend field. Save.
3. Paste your **Twilio Account SID, Auth Token, From Number**. Save.
4. Set **Officer Alert Email** — where new application + contact-form notifications go.
5. **Send a test email** to confirm Resend works.

### 12.2 Officer & content basics
1. **Officers** — add at least the President / VP / Secretary with photos.
2. **Club Stats** — update member count, miles maintained, etc.
3. **Sponsors** — add current sponsors with logos.
4. **Registration Form** — pick which optional fields to show.
5. **Email Templates → New Template** — make at least one branded template, send a test to yourself.

### 12.3 Trail map
1. **Manage Panel → Trail Map → Draw New Trail**.
2. Click points along a trail; double-click to finish.
3. Set the name, status (Open/Closed/Caution/Groomed/Planned), and visibility (Public/Members/Both).
4. Save. The trail now shows on the public **Map** page (`/map/`), colored by status.
5. Each trail has a **Download GPX** button — members import that file into the Polaris Off Road / Ride Command app, OnX, Gaia, or Garmin to navigate it.

**Photo geotags:** when you upload photos to announcements, trail conditions, or trail work logs, the GPS coordinates baked into the photo by your phone's camera are extracted automatically. Those photos appear as pins on the public Map page. Members' phones must have **Location → Camera = On** for this to work.

### 12.4 Optional: Social link preview
Settings → Communications → **Social / Link Preview** section. Upload a 1200×630 image of your club logo — this shows up when someone shares the site on Facebook/iMessage.

---

# Part 13 — Editing the code (the daily workflow)

This is the part beginners worry about. It's actually simple:

```
Edit on your laptop → Push to GitHub → SSH to VPS → ./build.sh
```

### 13.1 The pattern in detail

**On your laptop** (in VSCode terminal):

```bash
cd ~/Desktop/yourclub-website
git pull                          # get the latest from GitHub (in case server changed something)
# ...edit files in VSCode...
git add .
git commit -m "Brief description of what I changed"
git push origin main
```

**On the VPS** (via SSH):

```bash
cd ~/snodeos
./build.sh
```

That's it. ~5 minutes from edit to live.

### 13.2 Quick-restart flags

`./build.sh` accepts shortcuts:

| Flag | What it does | When to use |
|------|--------------|-------------|
| (no flag) | Full deploy: pull, rebuild, migrate, seed | After any code change |
| `-n` | No rebuild — just restart containers | After only `.env` edits |
| `-g` | Skip git pull — deploy local-only changes | Testing changes on the server you haven't pushed yet |
| `-c` | Just run Django's system check | Sanity-checking before a real deploy |
| `-s` | Re-run seed_data only | After deleting seed content by mistake |

### 13.3 Using Claude or ChatGPT to write code

The honest workflow most people use:

1. Open the file you want to change in VSCode.
2. Copy the file's contents (Ctrl+A, Ctrl+C) into Claude/ChatGPT.
3. Tell it what you want: *"Change the home page so the announcements section comes BEFORE the about section"*.
4. The AI gives you the edited file back.
5. Paste it back into VSCode (Ctrl+A to select, Ctrl+V to replace).
6. Save (Ctrl+S).
7. In VSCode terminal: `git add . && git commit -m "Reorder home page" && git push`.
8. SSH to VPS, `./build.sh`.

If you have the Claude Code extension installed, steps 1–6 become **right-click → Claude → Edit** — much smoother.

### 13.4 If you break something

```bash
git log --oneline -5    # see recent commits
git revert HEAD         # undo the most recent one
git push origin main
```

Then re-run `./build.sh` on the VPS. You're back to before.

If migrations broke the database, restore from the snapshot:

```bash
# On the VPS, in the snodeos folder
ls backups/                                                    # find the right .sql.gz file
gunzip -c backups/snodeos-20260519-201700.sql.gz | docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

---

# Part 14 — Troubleshooting

### Site shows "502 Bad Gateway"
The Django container probably crashed. On the VPS:
```bash
docker compose logs -f web
```
Look for a red `Error` message. The error usually tells you exactly what's wrong (missing env var, bad migration, etc.).

### Emails aren't sending
1. Go to **Manage Panel → Email Log** in the site. Look for failed rows — the error message tells you why.
2. Common causes: Resend API key typo, domain not verified in Resend yet, sender address doesn't match a verified domain.

### Can't SSH after enabling firewall
You probably blocked Tailscale by accident. From the DigitalOcean web console (the "Access" tab in the Droplet page), open a browser-based root shell and run `sudo ufw disable` to reset, then redo Part 6 carefully.

### Cloudflare Tunnel says "Bad Gateway" or won't connect
Check that the tunnel's hostname target is exactly `http://nginx:80` (the container name from docker-compose.yml, not localhost).

### Forgot which DB user/password is in `.env`
On the VPS: `cat ~/snodeos/.env | grep POSTGRES`.

---

# Checklist

Print this. Tick boxes as you go. Each box is ~5–20 min.

## Accounts
- [ ] GitHub account
- [ ] Cloudflare account
- [ ] Domain name purchased (Cloudflare or transferred to Cloudflare)
- [ ] DigitalOcean account
- [ ] Resend account
- [ ] Twilio account
- [ ] Tailscale account
- [ ] (Optional) Claude or ChatGPT account

## Laptop
- [ ] VSCode installed
- [ ] Git installed
- [ ] `git config user.name` and `user.email` set
- [ ] Tailscale installed and logged in
- [ ] SSH key generated (`~/.ssh/id_ed25519`)
- [ ] SSH public key added to GitHub
- [ ] Repo forked on GitHub
- [ ] Repo cloned to laptop
- [ ] (Optional) Claude/ChatGPT extension installed in VSCode

## Domain & DNS
- [ ] Domain showing as **Active** in Cloudflare

## VPS
- [ ] DigitalOcean Droplet created (Ubuntu 24.04, $6/mo, SSH key auth)
- [ ] Initial SSH login confirmed
- [ ] Tailscale installed on VPS and visible in your Tailnet
- [ ] Tailscale IP noted down
- [ ] Public SSH blocked / Tailscale-only access verified (optional but recommended)
- [ ] Docker installed (`docker --version` works without `sudo`)

## Cloudflare Tunnel
- [ ] Tunnel created in Cloudflare Zero Trust
- [ ] Public hostname route points to `http://nginx:80`
- [ ] Tunnel token copied for use in `.env`

## Resend
- [ ] Domain added to Resend
- [ ] DNS records added in Cloudflare for SPF/DKIM
- [ ] Domain shows **Verified** in Resend
- [ ] API key created and saved

## Twilio
- [ ] Phone number purchased
- [ ] Account SID + Auth Token saved
- [ ] (Optional) Webhook URL configured at `https://yourclub.com/webhooks/twilio/sms/` for two-way replies

## Deploy
- [ ] Repo cloned onto VPS
- [ ] `.env` file created from `.env.example` and filled in
- [ ] `./build.sh` ran successfully end-to-end
- [ ] Site loads at `https://yourclub.com` over HTTPS
- [ ] Superuser created (`createsuperuser`)
- [ ] Logged into `/manage/`

## Configuration
- [ ] Resend API key entered in Communications page
- [ ] Twilio credentials entered in Communications page
- [ ] Officer Alert Email set
- [ ] Test email sent and received
- [ ] At least one Officer added
- [ ] Club Stats updated
- [ ] At least one Email Template created and tested
- [ ] Social link preview image uploaded (or default kept)

## Editing workflow proven
- [ ] Made a small edit on the laptop (e.g. change a heading)
- [ ] `git push` succeeded from laptop
- [ ] `./build.sh` on VPS pulled and deployed the change
- [ ] Change visible on the live site

---

**Welcome to running a self-hosted club site.** From here on, you're just editing files and running `build.sh`. The hard part is done.
