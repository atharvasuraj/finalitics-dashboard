# Supported local interface

The Flask application is created by `create_app(test_config=None)` in `app.py`. Runtime configuration uses `DATA_DIR` (default: repository-relative `data/local`) and a 1 MB `MAX_CONTENT_LENGTH`. Test configuration overrides these in-process; uploads never choose filesystem paths. Paths do not depend on the launcher's current working directory.

| Endpoint | Behavior |
| --- | --- |
| `GET /` | Redirect to `/portfolio-analyser` |
| `GET /portfolio-analyser` | Supported HTML screen; available even before data preparation |
| `POST /portfolio-analyser-upload` | Multipart `file`, a `.csv` allocation with `Symbol,Weight` |
| `GET /portfolio-sample` | Same analysis for `samples/portfolio.csv` |
| `GET /sample-portfolio.csv` | Download that sample allocation |
| `GET /health` | `ready` + snapshot checksum (200), or `data_unavailable` + explanation (503) |
| `GET /legacy`, `GET /stock-offerings-page` | Explanation of disabled offerings; no legacy action controls |
| `/upload`, `/sample-data`, `/stock-offerings`, `/personal-mf`, `/personal-mf-table` | GET/POST return 410 JSON; no computation or fabricated performance |

Successful analyser JSON contains:

- `metrics`: `total_return`, `cagr`, `annualized_volatility`, `max_drawdown` as fractional values, without display rounding. Drawdown is a positive loss magnitude.
- `allocations`: canonical `symbol` and normalized `weight_percent`, sorted by symbol.
- `series`: `{date: "YYYY-MM-DD", index: number}` points on actual shared trading dates.
- `period`: `start`, `end`, and common `observations`.
- `dataset`: saved metadata including coverage and SHA-256 of the CSV bytes.
- `assumptions`: human-readable calculation limits.
- `chart`: base64 PNG of the historical index; there is no forecast segment.

There are no `llm_analysis`, `tech_data`, or forecast response fields. The archived React finance components are not compatible with this new contract and are not invoked by its entry point.

Errors are `{ "error": "readable explanation" }`: 400 for input, 413 for upload size, 503 for unusable saved data, 410 for disabled legacy computation, and a generic 500 for unexpected failures (details stay in the local server log). The browser renders errors and all variable text with `textContent`, clears stale results while analysing, and re-enables controls after failures. Uploaded allocations are parsed in memory and not saved.

The preparation script alone imports yfinance. Flask does not fetch data, read `.env`, import legacy financial modules, or call an LLM. A checksum is an integrity/reproduction identifier, not a signature or independent certification of provider accuracy.

## Dashboard API (October 2026 expansion)

- `GET /dashboard`: current UI; `/` now redirects here.
- `POST /dashboard/csv`: multipart `file`; returns validated canonical `{symbol, weight}` rows for the editor, without calculating or fetching history.
- `POST /dashboard/analyse`: JSON `source` (`saved`/`historical`), inclusive `start`/`end`, `current` and optional `alternative` arrays of `{symbol, weight}`. Defaults are the saved 2022–2024 range. Returns server-generated `analysis_id`, aligned `dates`, named `portfolios` (metrics, allocations, normalized `index`, negative percentage `drawdown`), actual `period`, per-symbol `coverage`, `excluded_dates`, provenance and assumptions. Calculation exceptions use the same 400/503 handling as the foundation.
- `POST /dashboard/interpret`: JSON `analysis_id`; uses server-retained facts only. Returns `status: ready` with validated `sections`, or `status: unavailable` with a safe explanation. Expired/unknown reports return 400; unavailable Gemini returns 200 and does not affect results.

The baseline API remains intact; the original calculator's three-stock CSV restriction still applies there. The dashboard parser supports broader NSE allocations, with ten distinct stocks across both portfolios. See `docs/DASHBOARD.md` for alignment, cache and LLM constraints. `/health` continues to report foundation snapshot readiness, not external-provider health or dashboard benchmark-cache readiness.

### Final UI polish

Successful commentary retains flattened `sections` and additionally returns `section_details`, keyed by topic, containing `summary` and server-supplied `facts` (`label`, `value`). This allows separate numerical-source presentation without parsing prose in JavaScript. Benchmark weight facts are omitted from generation vocabulary. Model, credentials, timeout, calculations and saved data are unchanged. The browser coordinator invalidates requests on edits and checks analysis ownership before rendering; aborting fetch does not guarantee cancellation of server work.
