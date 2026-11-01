# Restoration evidence — 31 October 2026

This record separates observed behavior of the original team prototype from the later restoration. It does not certify every original feature or infer individual ownership.

## Baseline inspection

Repository: `atharvasuraj/FINANCEKVGAI`, a fork of `OmkarShr/FINANCEKVGAI`. Restoration starts from `fc55e2930c8e2a0d43762f9b5122d365faf808cd` and preserves its Git history. Work is on `codex/historical-portfolio-demo`; source changes are uncommitted at initial verification. Source hashes in the verification JSON identify the actual restored implementation, separately from the original Git HEAD.

The original `app.py` can be read without reverting changes:

```bash
git show fc55e2930c8e2a0d43762f9b5122d365faf808cd:app.py
```

Inspected the three original notebooks without executing them:

- `FinalSubmissionFin.ipynb`: Morningstar holdings acquisition and conversion; saved output includes a NameError. It does not contain a financial multi-LLM orchestration pipeline.
- `google_generative_ai.ipynb`: Gemini/LangChain integration examples, predominantly Gemini 2.0 Flash; Gemini 2.5 preview identifiers appear in explanatory text. This does not verify a working Gemini 2.5 Pro finance integration.
- `sql_csv.ipynb`: SQL/Pandas agent examples over Titanic data, including saved outputs. These show exploration of agent tooling, not an integrated finance system.

The supplied internship report describes the portfolio analyser on page 8, uses future tense for LangChain orchestration on page 9, and lists strategy backtesting as future work on page 11. Its broader architecture and completion claims are not treated as proof of functioning software. This inspection cannot establish everything the team may have attempted elsewhere.

### Original runtime observations

Started with no Google key, after installing the original imports (the original requirements file listed only yfinance). Flask was started explicitly on loopback, without its default debug/public bind. The missing `ind_nifty100list.csv` warning appeared at startup. No production deployment was attempted.

| Surface | Observed result |
| --- | --- |
| Flask home, analyser upload page, stock-offerings page | HTML rendered |
| Flask sample-data action | Produced fund-performance numbers from randomly generated prices; these are not historical results |
| Stock-offerings action | HTTP 200 with an error and empty baskets; the screen displayed a loading-data failure |
| Custom allocation (`POST /personal-mf`) | HTTP 500 because `ind_nifty100list.csv` was missing |
| Analyser upload with wrong headers | HTTP 400; valid live-data analysis was not relied on for baseline evidence |
| Original `/health` | HTTP 200 even though the stock dataset was missing |
| React home and sample-data action | Rendered; sample used the same unsupported fund-performance backend |
| React Market Intelligence | Blank screen after `TypeError: Cannot read properties of undefined (reading 'total_market_cap')` |

See [baseline route results](evidence/original-routes.json), [original Flask sample](evidence/original-flask.jpg), [original React sample](evidence/original-react.jpg), and [original stock-screen failure](evidence/original-stock-failure.jpg). Random baseline fund numbers vary between requests and must not be compared with restored stock metrics.

## Restored workflow and provenance

The supported path is `GET /portfolio-analyser`, with sample or multipart CSV analysis. Runtime only reads saved prices and has no yfinance/Gemini integration. Legacy analysis endpoints return 410. The old React entry point now displays an archive notice; original financial components and notebooks remain as references.

Yahoo data was retrieved at **13:35:54 IST on 31 October 2026**. Each of the three stocks has **739** observations from **2022-01-03 through 2024-12-31** (2,217 stock-date rows). The snapshot uses provider-adjusted closing prices in INR, not fund NAVs. Its CSV SHA-256 is:

```text
6b1277ad97d9590c41b794caddee1496e12a7100bca96aba5a7864620a700aab
```

The [public manifest](../data/snapshot-manifest.json) records source, parameters, yfinance version, coverage, and retrieval time. Actual prices and their matching metadata remain under ignored `data/local/`. A saved snapshot is needed to reproduce these exact values; a fresh download may be revised by the provider. No public raw-data redistribution is assumed.

### Measured sample

Initial weights: Reliance 40%, HDFC Bank 30%, Infosys 30%. No rebalancing; index starts at 100; dividend/split-adjusted return proxy, no fees/taxes/contributions. Calendar CAGR and sample daily-return volatility use the formulas in the README.

| Metric | Result |
| --- | --- |
| Total return | 12.7156827787% |
| CAGR | 4.0810615610% |
| Annualized volatility | 17.0305583105% |
| Maximum drawdown (loss magnitude) | 16.8789734987% |
| Terminal index | 112.7156827787 |

These results describe this chosen historical example. No forecasting, strategy backtest, benchmark comparison, investment-performance improvement, or recommendation is claimed.

## Verification

Environment: macOS, Python 3.12.14; runtime pins Flask 3.1.3, pandas 3.1.0, NumPy 2.5.4, matplotlib 3.11.2. The preparation used yfinance 1.7.0. A separate clean temporary environment installed **only** `requirements.txt` and reproduced the real-data Flask sample/upload check without yfinance or a Gemini SDK installed. Data-preparation dependencies were then added to that environment, and a second download to a temporary directory succeeded. It returned the same coverage but a different checksum and very small numerical differences (total return 12.7156780379% versus the recorded 12.7156827787%). The original working-copy snapshot and manifest were retained. This demonstrates why exact reproduction uses saved bytes rather than a new provider request. Provider dependencies emitted nonfatal deprecation warnings during preparation.

Reproduction commands, from the activated environment:

```bash
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python -m pytest -q
python scripts/verify_snapshot.py
bash -n start.sh start_platform.sh
node --check static/portfolio.js
```

The unit/integration suite covers hand-computed normalization/returns, buy-and-hold versus daily rebalancing, calendar CAGR, known drawdown, constant prices, row/column order invariance, rounding/aliases, invalid CSV/weights/symbols, missing/gapped/duplicate prices, checksum/metadata corruption, sample/upload equality, upload size, readiness failures, and disabled legacy routes. These fixtures are explicitly synthetic; none is used by the demonstration.

All tests block Python DNS and TCP connections. `verify_snapshot.py` does the same before importing Flask and removes `GOOGLE_API_KEY`; it compares full sample/upload responses, including dated series and chart. This is an application-level offline verification, not an operating-system firewall audit. The local app also uses only local CSS/JS and embedded chart images.

Artifacts:

- [Numerical/API test output](evidence/tests.txt)
- [Real-data offline verification and source hashes](evidence/verified-results.json)
- [Independent clean-runtime verification](evidence/clean-runtime-results.json)
- [Clean data-preparation result and download comparison](evidence/clean-preparation.json)
- [Successful browser screen](evidence/restored-success.jpg)
- [Invalid-weight browser error](evidence/restored-error.jpg)

Browser checks verified the 739-observation result and all four displayed metrics, successful upload of the downloadable sample CSV, an 80%-weight error with stale results hidden, and successful recovery by loading the sample. No browser console errors were recorded on the restored analyser. The archived React notice was verified and `npm run build` passed; the supported demo does not require React. The legacy frontend's stale Browserslist database warning is unrelated to the Flask runtime and was not expanded into a dependency-upgrade project.

## Limits and presentation

Only this historical workflow is restored. Corporate-action adjustments are vendor supplied, missing dates shared by all three histories are not independently detected, and stocks/weights/dates were selected retrospectively for illustration. There is no point-in-time security universe, predictive validation, strategy selection test, live API reliability guarantee, functioning deployment, or production-infrastructure claim.

The 2025 work remains credited to Atharva, Kevin (`nabujika`), and Omkar (`OmkarShr`), with no strict ownership division. The 2026 restoration, tests, saved dataset, and documentation are later work. [Description drafts](PROJECT_DESCRIPTIONS.md) provide IT- and finance-focused wording using those boundaries; no resume was edited.
