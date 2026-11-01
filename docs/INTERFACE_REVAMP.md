# Interface revamp — 1 November 2026

This is October–November 2026 development of Finalitics, separate from the May–July 2025 collaborative internship prototype. The original local checkout remains based on `fc55e2930c8e2a0d43762f9b5122d365faf808cd`; the revamp is uncommitted at the time of this record. No new investment-performance or forecasting claim is introduced.

## What changed

- `/` is a new editorial home page with a saved-history preview, current/alternative switch and pointer/keyboard date inspection. It reads only `/home-preview`, which calculates the fixed locally saved example; it does not retrieve prices or call Gemini. Metrics, dates and counts stay pending until the actual response arrives. Missing data produces an explicit unavailable state, never a substitute curve.
- `/dashboard` is the portfolio workspace. Build, Explore and optional AI interpretation are distinct stages. Overview, Risk & allocation and Compare mixes present the calculated results; input allocation graphics describe the weights being edited. The same corrected calculations, validation, matching-date comparison, CSV handling and stale-request protections remain in use.
- `/dashboard?example=1` opens the guided saved example directly. Other stocks and date ranges still require an explicit historical retrieval or an existing exact-request cache entry.
- The visual system uses warm paper, dark ink, cobalt and lime with responsive layouts, local SVG charts, restrained transitions and reduced-motion support. No remote fonts, chart CDN, forecasting or agent framework was added.

## Calculate control and stale interface

The running server served an older cached template alongside newer JavaScript; the served page lacked 17 controls expected by the controller. A controller referencing the wrong controls can stop the Calculate action, while old CSS can conceal a visual update. The app now enables template reloading, versions local asset URLs and sends `no-store` for HTML/CSS/JavaScript responses. Controller/template wiring and calculation-state regressions are included in automated checks; actual browser behavior still needs the verification below.

The user-owned server needs **one restart on the existing port** to load these Python changes. In the same Terminal, press Control+C, run `PORT=5002 ./start.sh`, then reload `http://127.0.0.1:5002/`. Exported key/model settings remain in that Terminal. No different port or key re-entry is required. Source edits after this restart receive new asset versions; templates reload automatically.

## Evidence and verification status

| Check | Current status |
| --- | --- |
| Python numerical, validation, route and Gemini-mock suite | 68 passed |
| JavaScript state, controller and home-preview suite | 20 passed |
| Saved and cached-custom reproduction with Python networking blocked | Passed; saved/current metrics match the foundation exactly |
| JavaScript syntax and whitespace checks | Passed |
| Desktop/mobile/print verification of this revamp | Pending local-browser permission |
| New home/workspace screenshots | Pending browser verification; none claimed |

Commands from the repository root:

```bash
python -m pytest -q
node --test tests/*.test.mjs
python scripts/verify_dashboard.py
python scripts/verify_snapshot.py --output /tmp/foundation-check.json
git diff --check
```

The Node glob is intentional: run every JavaScript test file, rather than only the older state suite. Node 20+ is needed for these checks, not for the app. The dashboard verifier additionally requires the cached TCS/Infosys 2021–2023 comparison described in [QUICKSTART](../QUICKSTART.md). No live Gemini call is needed for UI verification.

The retained saved snapshot's reproduction target is 739 matching observations, 2022-01-03 through 2024-12-31. Current 40/30/30 Reliance/HDFC Bank/Infosys allocation: 12.72% return, 4.08% CAGR, 17.03% annualized volatility, 16.88% maximum drawdown. Alternative 20/40/40: 13.39% return and 19.41% maximum drawdown. These are rounded historical snapshot results, not newly claimed improvements. The offline rerun confirmed agreement with these retained results; source hashes are recorded in `docs/evidence/dashboard-verification.json`.

Browser access was blocked by the local-origin permission gate. That is an outstanding verification limit, not a passed visual check. Do not use older screenshots in `docs/evidence/` as screenshots of this revamp. Once access is available, verify home loading/unavailable/success states; the guided example and Calculate action; invalid weights and CSV recovery; stale results; scenario/tabs/charts; mobile overflow/focus; and print output. Save new screenshots only from this version.

## Data and attribution boundaries

Downloaded stock-price snapshots and caches under `data/local/` are prepared locally and Git-ignored. A fresh public clone has no prices; prepare the data online once or restore privately retained matching snapshot bytes before demonstrating offline. Vendor updates may change re-downloads. The preview uses adjusted **stock-price** observations, not mutual-fund NAVs.

Financial assumptions and limitations are unchanged: normalized initial holdings, fractional units, buy and hold, no cash flows/rebalancing/fees/taxes, shared observed dates, and an adjusted-price return proxy. NIFTYBEES is an INR ETF reference with fees/tracking effects, not the official NIFTY total-return index. Gemini remains optional LLM-assisted interpretation; qualitative claims are not independently certified.

Original team credit belongs to Atharva Suraj Krishnan, Kevin Felix Dcunha (`nabujika`) and Omkar Shrikanth (`OmkarShr`); Kevin and Omkar wrote more of the original code. The upstream [OmkarShr/FINANCEKVGAI](https://github.com/OmkarShr/FINANCEKVGAI) relationship remains explicit. Commit counts do not establish individual ownership. This UI work must be described as later restoration/development, not as completed during the 2025 internship. No resume was edited.
