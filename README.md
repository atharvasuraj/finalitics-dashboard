# Finalitics — your portfolio lab

Start with an interactive home page, then build your mix → explore the results → request AI interpretation. The portfolio workspace has a live allocation ring, a guided saved example, equal-weight shortcut and focused Overview, Risk & allocation, Compare mixes and AI views.

A local portfolio-analysis dashboard built by restoring and modestly extending a collaborative KVGAI Tech internship prototype. It compares current and alternative **buy-and-hold NSE stock allocations** with an INR NIFTY ETF reference, using actual matching dates and adjusted historical prices. Optional Gemini commentary interprets calculated facts; it does not forecast or recommend trades.

## Start

Tested with Python 3.12.14:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python scripts/prepare_data.py       # first setup only; do not overwrite an existing snapshot
python scripts/prepare_dashboard.py  # first setup only: saved benchmark cache
PORT=5002 ./start.sh
```

Open [Finalitics](http://127.0.0.1:5002/), [the workspace](http://127.0.0.1:5002/dashboard), or [the guided example](http://127.0.0.1:5002/dashboard?example=1). The current working copy already has its saved data; use `PORT=5002 ./start.sh` directly. `./start.sh` without a port uses 5001. No Node packages or external chart CDN are required to run the app.

See [QUICKSTART](QUICKSTART.md) for optional Gemini setup, updating an existing server and a short walkthrough; [dashboard methods and evidence](docs/DASHBOARD.md) for calculations; [interface revamp evidence](docs/INTERFACE_REVAMP.md) for the latest UI verification status.

## Current features

- Home page with an interactive saved-history preview, allocation switching and keyboard/pointer date inspection. Metrics and coverage stay blank until the actual local response arrives; missing data never produces a substitute chart.
- Saved 2022–2024 example, plus historical retrieval/cache for up to ten distinct NSE/INR stocks across both allocations. No FX conversion.
- Editable weights and CSV import into either allocation; canonical aliases such as `TCS` and `TCS.NS` merge consistently. Live totals and hints complement server validation.
- Current, optional alternative and `NIFTYBEES.NS` reference compared over one shared observed-date intersection. Coverage and excluded-date counts are disclosed. At least 252 matching observations are required.
- Interactive performance, drawdown and allocation charts, keyboard date inspection, summary metrics and scenario deltas in **percentage points**.
- Input revisions and analysis IDs guard asynchronous results. Editing inputs invalidates commentary; late responses cannot overwrite a new report.
- User-initiated Gemini 3.5 Flash-Lite commentary with separate prose and server-valued facts. An earlier live saved-example response succeeded in 2 seconds. Numerical sourcing is checked; qualitative interpretation is not independently certified. Model and key remain server environment settings.
- Browser print/save-PDF styling for the current, non-stale report; no separate PDF service.

## Calculations and limits

`I(t) = 100 × Σ[w_i × P_i(t)/P_i(t0)]`. Fractional initial holdings, no rebalancing, flows, fees, taxes or slippage. Weights drift after inception. Adjusted prices are a vendor dividend/split-adjusted return proxy, not actual account cash flows or mutual-fund NAVs.

| Metric | Definition |
| --- | --- |
| Total return | `I(last)/I(first) - 1` |
| CAGR | `(I(last)/I(first)) ** (365.25 / elapsed calendar days) - 1` |
| Annualized volatility | Sample standard deviation of consecutive observed returns × `sqrt(252)` |
| Maximum drawdown | Largest `1 - I(t)/running_peak(t)`; positive loss magnitude |

Dashboard comparisons intersect valid histories without filling quotes or dropping symbols. Internal missing quotes, nonpositive/nonfinite values, duplicates and insufficient overlap fail explicitly. Dates absent from every history are not detected without an independent exchange calendar; annualization of irregular intersections is approximate. Adding an alternative can change the shared period and therefore measured results. The original foundation calculator retains its stricter gap rejection.

NIFTYBEES is an investable ETF with fees/tracking effects, not the official NIFTY total-return index. Retrospectively chosen examples do not establish investment-performance improvements. Corporate actions are vendor supplied and not independently audited.

Saved 40/30/30 Reliance/HDFC/Infosys example, 739 matched observations (2022-01-03–2024-12-31): total return **12.72%**, CAGR **4.08%**, volatility **17.03%**, max drawdown **16.88%**. The 20/40/40 alternative returns **13.39%** with **19.41%** max drawdown; these are historical trade-offs, not an optimization claim.

Prices and caches remain Git-ignored under `data/local/`. New clones need one online preparation step or a privately retained snapshot. Provider revisions can change re-downloads. See [provider-use guidance](https://ranaroussi.github.io/yfinance/) before redistributing downloaded data.

## Verification

```bash
python -m pytest -q
node --test tests/*.test.mjs
python scripts/verify_dashboard.py
python scripts/verify_snapshot.py --output /tmp/foundation-check.json
```

Current revamp totals: **70 Python checks and 20 JavaScript checks passed**. Node 20+ is needed only for JavaScript regression checks. Financial/API tests block Python networking; the offline dashboard reproduction additionally needs the already cached TCS/Infosys 2021–2023 example (instructions in QUICKSTART). Browser verification of this revamp is **pending permission**; it is not screenshot-validated. Older screenshots and the [final polish record](docs/FINAL_POLISH.md) describe earlier interfaces. See the [current evidence record](docs/INTERFACE_REVAMP.md). Original numerical calculations and saved data are unchanged.

## History and credit

The **May–July 2025 KVGAI Tech internship** was collaborative work by **Atharva Suraj Krishnan**, **Kevin Felix Dcunha ([nabujika](https://github.com/nabujika))**, and **Omkar Shrikanth ([OmkarShr](https://github.com/OmkarShr))**. There was no strict division of responsibilities; Kevin and Omkar wrote more of the original code. Commit counts do not establish individual ownership.

This is Atharva's fork of [OmkarShr/FINANCEKVGAI](https://github.com/OmkarShr/FINANCEKVGAI). Restoration, dashboard expansion and validation are **October–November 2026** work and must not be attributed to the internship period. Original notebooks and Git history are preserved, starting from `fc55e2930c8e2a0d43762f9b5122d365faf808cd`.

The retained [foundation calculator](http://127.0.0.1:5002/portfolio-analyser) uses the original three-stock saved workflow. Legacy fund-performance, allocation-generation and forecasting actions are disabled. [Original inspection evidence](docs/RESTORATION.md) is historical, not a current test summary. [IT/finance description drafts](docs/PROJECT_DESCRIPTIONS.md) preserve these boundaries; no resume is edited.

## Hosted demonstration

This standalone repository contains the November 2026 interface revamp. [Vercel deployment notes](docs/DEPLOYMENT.md) explain private saved-data bundling, ephemeral caches and optional server-side Gemini. The source repository intentionally contains no downloaded prices or keys.
