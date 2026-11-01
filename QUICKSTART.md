# Finalitics: run and demonstrate

## Setup

Use Python 3.12 (tested 3.12.14). From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python scripts/prepare_data.py
python scripts/prepare_dashboard.py
PORT=5002 ./start.sh
```

This working copy already has data: skip preparation and run `PORT=5002 ./start.sh`. A fresh clone has **no downloaded prices or cache**; complete the preparation steps locally. First-time downloads need internet; saved comparisons then run offline. Preparation refuses to overwrite the foundation snapshot; `--replace` is an explicit re-download that may change results. Retain `data/local/prices.csv`, matching `metadata.json`, and `data/local/cache/` privately for reproduction. These are Git-ignored.

Open [the home page](http://127.0.0.1:5002/), [the workspace](http://127.0.0.1:5002/dashboard), or [the guided saved example](http://127.0.0.1:5002/dashboard?example=1). Running `./start.sh` without `PORT` uses 5001. Launchers bind to loopback, do not kill other servers, and do not install packages. `requirements-data.txt` suffices without Gemini; `requirements-ai.txt` adds Gemini; `requirements-dev.txt` adds tests.

## Updating the existing server on port 5002

In the **same Terminal** running the old server, press Control+C once, then run:

```bash
PORT=5002 ./start.sh
```

Reload [Finalitics](http://127.0.0.1:5002/). This one restart loads the changed Python routes and asset helper. The existing exported Gemini key stays in that Terminal's environment; no key re-entry is needed. A different Terminal would need its own environment settings.

The previous server/browser could combine a cached JavaScript or stylesheet with a newer template, breaking control wiring or hiding visual changes. Templates now reload automatically and both pages use versioned local asset URLs. A normal reload after the restart should load the matching UI; use a hard refresh if an older page remains open. No port change is needed.

## Gemini (optional)

Use a key from a confirmed **Free project** if you require free-only usage. Project eligibility and quotas apply; the app cannot inspect billing status. Do not enable billing merely to use this demo. The current default remains **gemini-3.5-flash-lite**.

In zsh, enter the key privately in the same Terminal that starts the server:

```zsh
read -rs "GEMINI_API_KEY?Paste your local key, then press Enter: "
export GEMINI_API_KEY
export GEMINI_MODEL=gemini-3.5-flash-lite
printf '\n'
PORT=5002 ./start.sh
```

Stop an existing foreground server with Control+C first. Keys are not automatically loaded from `.env`. Never put them into chat, frontend code or Git. No Gemini call runs until you click **Generate interpretation**. A successful live saved comparison is recorded; UI regressions use mocks, with no billing or model changes. Failure states remain usable without AI.

## Three-minute walkthrough

1. **Home:** inspect the saved historical preview, switch allocations and move its date slider. Values appear only after the local dataset loads; a fresh clone without prepared data shows an explicit unavailable state.
2. **Build → guided example:** use **Explore the saved example** on the home page or **Take the guided example** in the workspace. The saved allocation and 2022–2024 settings load and calculate. Explain the actual 739 matching observations and index starting at 100.
3. **Allocation trade-off:** return to Build, edit current weights, observe the live allocation ring/totals and stale-result notice, then click **Calculate comparison**. Explore the current/alternative/ETF comparison. Return differences are percentage points; higher historical return can coincide with larger drawdown.
4. **Explore → Overview / Risk & allocation / Compare mixes:** hover/touch a chart or move its keyboard date slider. Switch the allocation chart; disable **Compare another mix** in Build to remove alternative inputs/choices.
5. **CSV:** expand **Import an allocation CSV**, then import `samples/portfolio.csv` into current weights. Other weights are preserved. Invalid totals are explained before submission and still checked by the server.
6. **AI:** request **Generate interpretation**. Read qualitative prose separately from server-supplied facts; numerical sourcing checks do not certify every interpretation. Editing inputs clears commentary. Optionally use **Export report** for the current report.

Rendered desktop, mobile and print checks for this revamp are pending local-browser permission; new screenshots are pending. Older evidence does not establish the new interface's visual quality. See [the current verification record](docs/INTERFACE_REVAMP.md).

## Reproduction and troubleshooting

```bash
python -m pytest -q
node --test tests/*.test.mjs
python scripts/verify_dashboard.py
```

The dashboard verifier needs the saved benchmark and a cached custom TCS/Infosys comparison. To populate that custom cache once online, use Retrieve history with TCS/Infosys 60/40 and alternative 40/60 over 2021-01-01–2023-12-31; calculate, then run the verifier offline. The foundation-only verifier needs no custom cache:

```bash
python scripts/verify_snapshot.py --output /tmp/my-foundation-check.json
```

Missing/corrupt data reports HTTP 503; restore saved bytes or prepare again. Invalid allocations report 400; uploads over 1 MB report 413. Saved mode supports only its three stocks; select Retrieve history for other stocks/dates. Cache entries are exact-request snapshots with no automatic refresh. Invalid Gemini output is discarded; 429 indicates quota/rate limits, 504 a timeout, and other safe categories distinguish access/provider errors. Do not repeatedly retry or switch billing during routine testing.

The old three-stock calculator remains at `/portfolio-analyser`; archived React components are not a second supported dashboard. `/health` describes foundation data readiness, not Gemini or provider health.
