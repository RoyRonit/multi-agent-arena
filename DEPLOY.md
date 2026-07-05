# Deploying The Roundtable — Railway + Cloudflare domain

The app is a single Docker image: FastAPI serves the API **and** the built React frontend on
one port. Railway builds the `Dockerfile` and runs it; Cloudflare provides the domain.

---

## 0. Before you deploy (do this first)

1. **Rotate your OpenRouter key.** The key currently in `.env` was shared in chat — treat it
   as compromised. Generate a fresh one at <https://openrouter.ai/keys>. Never commit `.env`
   (it's gitignored); you'll paste the new key into Railway's dashboard instead.
2. **Pick your access phrase.** Anyone with the URL can spend your credits, so the ASCII-captcha
   gate is on. Choose the phrase you'll set as `ACCESS_PHRASE` (e.g. a word you share only with
   the people you want to let in). Leave it unset only for a throwaway demo.

### Environment variables to set in Railway

| Variable | Value | Required |
|---|---|---|
| `OPENROUTER_API_KEY` | your **new** key | ✅ |
| `ACCESS_PHRASE` | the captcha word (e.g. `ROUNDTABLE`) | recommended |
| `AGENT_MODEL` | `google/gemini-2.5-flash` | optional |
| `CHAIRMAN_MODEL` | `anthropic/claude-sonnet-4.5` | optional |
| `DAILY_DEBATE_CAP` | e.g. `100` (0 = unlimited) | optional |

`PORT` is injected by Railway automatically — the Dockerfile already honors it.

---

## 1. Deploy to Railway

### Option A — Railway CLI (no GitHub needed)

```bash
npm i -g @railway/cli
railway login
cd "roundtable"
railway init            # create a new project
railway up              # builds the Dockerfile and deploys this directory
```

Then in the Railway dashboard → your service → **Variables**, add the env vars from the table
above → the service redeploys. Under **Settings → Networking → Generate Domain** you'll get a
public `https://<name>.up.railway.app`. Open it and confirm the captcha hero loads.

### Option B — GitHub

```bash
cd "roundtable"
git init && git add . && git commit -m "The Roundtable"
# create an empty GitHub repo, then:
git remote add origin git@github.com:<you>/roundtable.git
git push -u origin main
```

In Railway: **New Project → Deploy from GitHub repo** → pick the repo. Railway detects the
`Dockerfile`. Add the env vars, deploy, generate a domain.

> Note: `debates/*.json` is written to the container's ephemeral disk — fine for a POC (users
> download their own transcripts). Add a Railway Volume mounted at `/app/debates` if you want
> them to survive redeploys.

---

## 2. Connect your Cloudflare domain

1. Railway → service → **Settings → Networking → Custom Domain** → enter e.g.
   `roundtable.yourdomain.com`. Railway shows a **CNAME target** like
   `<something>.up.railway.app`.
2. Cloudflare dashboard → your domain → **DNS → Add record**:
   - **Type:** CNAME
   - **Name:** `roundtable` (the subdomain)
   - **Target:** the Railway CNAME target
   - **Proxy status:** **DNS only** (grey cloud) ← recommended
3. Wait for Railway to show the domain as **Active** (it issues a TLS cert). Visit
   `https://roundtable.yourdomain.com`.

### Why grey cloud (DNS only)?

The app streams over **SSE** (Server-Sent Events). Cloudflare's proxy (orange cloud) can buffer
streamed responses and complicates Railway's cert issuance. **DNS only** lets Railway terminate
TLS and stream cleanly — the domain still runs through Cloudflare's DNS.

Want Cloudflare's CDN/WAF in front later? Switch to orange cloud **after** the cert is Active,
set **SSL/TLS → Full (strict)**, and verify a debate still streams turn-by-turn (not all at once).

---

## 3. Post-deploy smoke test

```bash
curl https://roundtable.yourdomain.com/api/health
# -> {"ok":true,"key_set":true,...,"gate":true}
```

Then open the site, read the ASCII captcha, type the phrase, and run a debate. Done.
