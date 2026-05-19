# Brainerd Snodeos — Site Setup Guide

**Last updated:** May 2026  
This document is for club officers reviewing what the site does and what steps are needed to make it fully operational.

---

## What's Already Built

### Public Website

| Page | What It Does |
|------|-------------|
| **Home** | Hero image, club stats, about section, announcements, optional Facebook feed |
| **About** | Officers with photos, Directors section |
| **Trail Work** | Log of trail work sessions with photos (members must log in to view) |
| **Contact** | Contact form — submissions go to the officer inbox in the management panel |
| **Join** | Online membership application (fields configurable from the panel) |
| **Member Login / Password Reset** | Members can log in and reset their password via email |

### Member Dashboard

Members who have been approved get access to a private dashboard where they can:
- View their membership status
- Edit their profile and photo
- Change their password

### Management Panel (`/panel/`)

Only members with officer access can log in here. Everything is managed through this panel — no separate admin login needed.

| Section | What You Can Do |
|---------|----------------|
| **Dashboard** | Overview of members, pending applications, messages, trail work |
| **Club Stats** | Edit the headline numbers shown on the home page (members, miles maintained, budget, landowners) |
| **Announcements** | Post, edit, pin, and delete announcements. Choose visibility: Public, Members Only, or Both |
| **Trail Work** | Log trail work sessions with volunteer count, hours, notes, and photos |
| **Officers** | Add/edit/remove officers and their photos, titles, and sled brand |
| **Officer Titles** | Manage the list of officer titles (President, VP, etc.) |
| **Sponsors** | Add/edit/remove sponsors with logos and website links. Toggle active/inactive |
| **Pending Applications** | Review and approve or reject new member applications |
| **All Members** | View and manage all members, search by name or status |
| **Import Members** | Upload a CSV to bulk-import existing members |
| **Messages** | Read and manage contact form submissions |
| **Registration Form** | Control which fields appear on the signup form, mark them required or optional, and rename them |
| **Dues** | Track who has paid dues, mark paid/unpaid, bulk update, send email reminders |
| **Permissions** | Grant or revoke management panel access for any active member |
| **Facebook** | Configure the Facebook integration (see below) |
| **Email Members** | Compose and send an email to all active members at once |
| **Email Settings** | Configure the outgoing email server and send a test email |

---

## What Needs To Be Done Before Going Live

### 1. Email — Required for Almost Everything

Email is used for:
- New member application notifications to officers
- Contact form submission notifications
- Member password resets
- Dues reminder emails
- Email blasts to all members

**Current state:** Email is in "console" mode — it prints to server logs but does not actually send. You must configure an SMTP server.

#### Option A — Gmail (Free, Easiest)

Use a Google account dedicated to the club (e.g. `brainerdsnodeos@gmail.com`).

1. Log into that Google account
2. Go to **Google Account → Security → 2-Step Verification** and turn it on
3. Go to **Google Account → Security → App Passwords**
4. Create an App Password named "Snodeos Site" — copy the 16-character password
5. Add these to the server's `.env` file (or Docker Compose environment):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=brainerdsnodeos@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx   ← your 16-char app password
DEFAULT_FROM_EMAIL=Brainerd Snodeos <brainerdsnodeos@gmail.com>
NOTIFICATION_EMAIL=brainerdsnodeos@gmail.com
```

6. Rebuild the site (`./build.sh`) and test using **Settings → Email Settings → Send Test Email**

> **Note:** Gmail limits ~500 emails/day. Fine for club use.

#### Option B — SendGrid (Free up to 100/day, better deliverability)

1. Create a free account at [sendgrid.com](https://sendgrid.com)
2. Verify your sender domain (follow their DNS instructions)
3. Create an API key under **Settings → API Keys**
4. Add to `.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxx   ← your SendGrid API key
DEFAULT_FROM_EMAIL=Brainerd Snodeos <noreply@yourdomain.com>
NOTIFICATION_EMAIL=officers@youremail.com
```

#### Option C — Mailchimp Transactional / Mailgun

Both offer generous free tiers and are well-regarded for newsletters and clubs. Setup is similar to SendGrid — SMTP credentials from the dashboard, paste into `.env`.

---

### 2. Text Messages (SMS) — Optional, Not Yet Built

SMS is not currently built into the site. The most common tool for this is **Twilio**.

**What it would enable:**
- Dues reminders sent as text messages (in addition to or instead of email)
- Trail condition alerts
- Meeting reminders

**What it would cost:**
- Twilio account: free to set up
- Phone number: ~$1.15/month
- Each outgoing SMS: ~$0.0079 (about $0.80 per 100 texts)

**Steps to add Twilio:**

1. Create an account at [twilio.com](https://www.twilio.com)
2. Buy a US phone number from the Twilio Console
3. Copy your **Account SID** and **Auth Token** from the dashboard
4. Add to `.env`:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+12185550100
```

5. Let the developer know — the code to send texts in the dues reminder and email blast sections can be added once these credentials are in place. The Member model already stores phone numbers when that field is enabled on the registration form.

---

### 3. Facebook Integration — Optional

Two options are available, configurable under **Settings → Facebook** in the panel.

#### Option 1 — Facebook Page Plugin (Embed feed on home page)
Shows your club's recent Facebook posts directly on the home page.

1. Make sure you have a Facebook Page for the club (not a personal profile)
2. Go to **Settings → Facebook** in the panel
3. Choose **"Facebook Page Plugin"**
4. Paste your Facebook Page URL (e.g. `https://www.facebook.com/BrainerdSnodeos`)
5. Save — the feed will appear on the home page automatically

#### Option 2 — Zapier Auto-Post (Post announcements to Facebook automatically)
When you post a **Public** announcement on the site, it automatically gets posted to your Facebook page.

1. Create a free account at [zapier.com](https://zapier.com)
2. Create a new Zap:
   - **Trigger:** Webhooks by Zapier → Catch Hook
   - **Action:** Facebook Pages → Create Page Post
3. Copy the webhook URL Zapier gives you
4. Go to **Settings → Facebook** in the panel
5. Choose **"Zapier Auto-Post"**
6. Paste the webhook URL
7. Save — now every public announcement automatically posts to Facebook

> **Note:** The free Zapier plan allows 100 Zap runs/month, which is plenty for club announcements.

---

### 4. Cloudflare Tunnel — If Using a Home/Office Server

If the site is running on a home or office server (not a cloud VPS), a Cloudflare Tunnel bypasses the need to open firewall ports and provides a free HTTPS certificate.

1. Log into [cloudflare.com](https://cloudflare.com) and add your domain
2. Go to **Zero Trust → Access → Tunnels**
3. Create a new tunnel — copy the tunnel token
4. Add to Docker Compose `.env`:

```
CLOUDFLARE_TOKEN=eyJhxxxxxxxxxxxxxxxx...
```

5. Rebuild with `./build.sh`

---

### 5. Domain & DNS

If the site should be at `www.snodeos.com` (or any custom domain):

1. Log into your domain registrar (GoDaddy, Namecheap, etc.)
2. Point the domain's nameservers to Cloudflare (Cloudflare provides these when you add the domain)
3. In Cloudflare DNS, point the domain to your server IP or tunnel
4. Update the server's `.env`:

```
ALLOWED_HOSTS=snodeos.com,www.snodeos.com
CSRF_TRUSTED_ORIGINS=https://snodeos.com,https://www.snodeos.com
SITE_URL=https://snodeos.com
DEFAULT_FROM_EMAIL=Brainerd Snodeos <noreply@snodeos.com>
```

5. Rebuild with `./build.sh`

---

## Environment Variables Reference

All site configuration lives in a `.env` file (or Docker Compose environment) on the server. Here's a full reference:

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Django security key (must be unique, keep private) | `50-char random string` |
| `DEBUG` | Set to `False` in production | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed domain names | `snodeos.com,www.snodeos.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@db/snodeos` |
| `CSRF_TRUSTED_ORIGINS` | Domains allowed to submit forms | `https://snodeos.com` |
| `SITE_URL` | Full public URL (used in emails) | `https://snodeos.com` |
| `EMAIL_BACKEND` | Use `smtp` for real email | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | TLS encryption | `True` |
| `EMAIL_HOST_USER` | SMTP login email | `club@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password or app password | `xxxx xxxx xxxx xxxx` |
| `DEFAULT_FROM_EMAIL` | "From" name on outgoing emails | `Brainerd Snodeos <club@gmail.com>` |
| `NOTIFICATION_EMAIL` | Where officer alerts go (new apps, messages) | `officers@gmail.com` |
| `CLOUDFLARE_TOKEN` | Cloudflare tunnel token (if using tunnel) | `eyJh...` |
| `TWILIO_ACCOUNT_SID` | Twilio account ID (when SMS is added) | `ACxx...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token (when SMS is added) | `xxxx...` |
| `TWILIO_FROM_NUMBER` | Twilio phone number (when SMS is added) | `+12185550100` |

---

## Quick-Start Checklist

- [ ] Configure email (Gmail app password is the easiest first step)
- [ ] Send a test email from **Settings → Email Settings**
- [ ] Add your real officer names and photos in **Club → Officers**
- [ ] Update club stats in **Overview → Club Stats**
- [ ] Add current sponsors with logos in **Club → Sponsors**
- [ ] Post a welcome announcement in **Content → Announcements**
- [ ] Review and adjust the registration form fields in **People → Registration Form**
- [ ] Approve or import existing members in **People → All Members**
- [ ] Optionally enable Facebook integration in **Settings → Facebook**
- [ ] Update domain/DNS if pointing to a custom domain
- [ ] Set `DEBUG=False` in `.env` when ready for public use
- [ ] Contact developer when ready to add SMS/text reminders (Twilio)
