# ⬡ ResumeRank AI — ATS Resume Checker

A professional, AI-powered ATS Resume Checker website built with Python (FastAPI) and Claude AI.

---

## ✨ Features

- **AI-Powered ATS Scoring** (0–100) powered by Claude AI
- **Keyword Gap Analysis** — matched vs. missing keywords
- **Section-by-Section Scores** — Contact, Experience, Education, Skills, Formatting
- **Prioritized Action Plan** — High/Medium/Low suggestions with examples
- **Strengths & Quick Wins** — instant improvements
- **Rate Limiting** — 3 free checks/day per IP
- **File Support** — PDF, DOC, DOCX, TXT
- **Responsive Design** — works on mobile & desktop
- **Monetization Ready** — Free/Pro/Enterprise tiers

---

## 🚀 Quick Start (Local)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run the server
```bash
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open in browser
```
http://localhost:8000
```

> **Demo Mode**: If no `ANTHROPIC_API_KEY` is set, the app runs in demo mode with mock results.

---

## ☁️ Deployment Options

### Option A: Railway (Easiest — Free Tier Available)
1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables (`ANTHROPIC_API_KEY`)
4. Railway auto-detects Python and deploys. Done! 🎉

### Option B: Render (Free Tier)
1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add `ANTHROPIC_API_KEY` in Environment variables

### Option C: DigitalOcean App Platform
1. Push to GitHub
2. Create a new App, connect repo
3. Set `Run Command`: `uvicorn main:app --host 0.0.0.0 --port 8080`
4. Add environment variables

### Option D: VPS (Ubuntu)
```bash
# On your server:
git clone <your-repo> && cd ats-checker
pip install -r requirements.txt
cp .env.example .env && nano .env   # Add your API key

# Run with systemd or screen:
screen -S ats
uvicorn main:app --host 0.0.0.0 --port 8000

# Set up nginx reverse proxy pointing to localhost:8000
# Use Certbot for HTTPS
```

---

## 💰 Monetization Setup

### Stripe Integration
1. Create account at [stripe.com](https://stripe.com)
2. Create a Product → Subscription → $9/month
3. Get your Price ID (`price_xxx`)
4. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PRO_PRICE_ID=price_...
   ```
5. In `templates/pricing.html`, replace the `handleProSignup` function with a Stripe Checkout redirect

### Revenue Streams
- **Pro Plan** — $9/month (unlimited checks)
- **Enterprise** — Custom pricing for HR teams
- **Affiliate links** — Resume templates, job boards
- **Google AdSense** — Add ads for free-tier users

---

## 🏗 Project Structure

```
ats-checker/
├── main.py                  # FastAPI app, API endpoints, Claude integration
├── requirements.txt
├── .env.example             # Environment variables template
├── static/
│   ├── css/style.css        # All styles
│   └── js/main.js           # Frontend logic
└── templates/
    ├── index.html           # Main page (checker + results)
    └── pricing.html         # Pricing page
```

---

## 🔑 API Keys

| Service | Purpose | Where to Get |
|---------|---------|--------------|
| Anthropic | AI analysis | [console.anthropic.com](https://console.anthropic.com) |
| Stripe | Payments | [stripe.com](https://stripe.com) |

---

## 📈 Scaling Tips

- **Redis** — Replace in-memory rate limiting with Redis for multi-instance deployments
- **PostgreSQL** — Store user accounts and check history
- **Celery** — Queue long-running analysis jobs
- **CDN** — Put Cloudflare in front for global performance

---

## 📄 License

MIT License — Free to use, modify, and deploy commercially.
