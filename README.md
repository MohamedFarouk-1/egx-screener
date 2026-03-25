# EGX Upside Screener

A full-stack quantitative screener for Egyptian Exchange (EGX) stocks. Scores stocks on
**Valuation (35%) · Growth (30%) · Quality (25%) · Momentum (10%)** and ranks them by composite upside potential.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11 · FastAPI · yfinance · pandas |
| Frontend | React 18 · Tailwind CSS · Vite |
| Data | Yahoo Finance via yfinance (free, no API key) |
| Cache | In-memory, 6-hour TTL |

---

## Quick Start (Docker — recommended)

```bash
# Clone / unzip the project
cd egx-screener

# Build and run
docker compose up --build

# Open browser
open http://localhost:8080
```

The first data load takes **60–90 seconds** (fetching 53 tickers from Yahoo Finance).
The UI shows a loading banner and polls automatically.

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173 (proxies /api → localhost:8000)
```

---

## Deploy to Fly.io (free tier)

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly auth login
fly launch --no-deploy        # creates app, use existing fly.toml
fly deploy                    # builds + deploys
fly open                      # opens public URL
```

## Deploy to Render (free tier)

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your repo — Render auto-detects `render.yaml`
4. Click **Create Web Service**
5. Wait ~5 min for build + first data load

## Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
railway domain   # get your public URL
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/screener` | Full ranked stock list (JSON) |
| `GET /api/screener/csv` | Download CSV |
| `GET /api/screener/memo` | Plain-text 3-paragraph investment memo |
| `GET /api/health` | Health check + last refresh time |

---

## Scoring Methodology

### Metrics used

| Dimension | Weight | Metrics |
|---|---|---|
| Valuation | 35% | P/E, EV/EBITDA, P/B (inverse rank — cheaper = higher score) |
| Growth | 30% | Revenue growth YoY, ROE |
| Quality | 25% | ROE, Debt/Equity (inverse), Current Ratio |
| Momentum | 10% | 52-week return |

Each metric is **percentile-ranked (0–100)** within the surviving universe. Missing values are filled with sector medians, then universe medians.

### Flags

| Flag | Condition |
|---|---|
| `deep_value` | P/B < 1.0 |
| `overleveraged` | D/E > 2.0 |
| `liquidity_risk` | Current Ratio < 1.0 |

---

## EGX-Specific Risk Factors

- **FX Risk**: All valuations denominated in EGP; USD-equivalent shown as secondary column
- **Thin float**: Many EGX names have <20% free float → liquidity risk
- **Related-party risk**: Common in Egyptian conglomerates
- **Data lag**: yfinance EGX data may lag 1–2 quarters vs Arabic EFSA filings
- **High discount rate environment**: CBE policy rates >27% raise the equity hurdle rate

---

## Ticker Universe

53 EGX tickers screened (Yahoo Finance `.CA` suffix):

```
COMI, SWDY, TMGH, ETEL, MFPC, EAST, EGAL, ABUK, QNBE, ALCN, EFIH, FWRY,
HDBK, ORAS, EMFD, ADIB, EFID, HRHO, JUFO, GBCO, PHDC, EGCH, ORHD, SKPC,
CLHO, ARCC, TAQA, ORWE, PHAR, ISPH, CIRA, AMOC, DOMT, SUGR, OLFI, MICH,
EXPA, OCDI, MASR, LCSW, ENGC, KZPC, NAPR, ASCM, ECAP, SCEM, MBSC, MCQE,
EFIC, MTIE, VALU, HELI, CSAG
```

---

*Not investment advice. Data via Yahoo Finance. Always verify with EFSA Arabic filings.*
