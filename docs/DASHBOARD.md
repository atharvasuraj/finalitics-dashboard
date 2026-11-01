# Dashboard method and evidence — October 2026

The current setup and walkthrough are in [QUICKSTART](../QUICKSTART.md). The dashboard is at `/dashboard`; `/portfolio-analyser` is the retained three-stock foundation calculator. Final polish does not change the numerical engine, source prices, cache policy, benchmark, Gemini model or request timeout.

## Data and calculations

Historical mode accepts NSE/INR stocks and inclusive dates ending before today, with a maximum ten-year range and ten distinct stocks across current/alternative. Saved mode locks 2022–2024 dates and uses Reliance, HDFC Bank and Infosys plus a cached NIFTY ETF. A zero-weight row is still validated/retrieved; remove unused rows.

Yahoo/yfinance requests use daily `Adj Close`, `auto_adjust=False`, `back_adjust=False`, `repair=False`, `keepna=True`, and actions. Currency/timezone must be INR/Asia-Kolkata. Corporate actions remain vendor supplied. This is an adjusted-price return proxy, not mutual-fund NAV history or an actual cash account. ETF fees/tracking affect `NIFTYBEES.NS`; it is not the official NIFTY total-return index.

Cache files combine exact symbol/date request, CSV, SHA-256, retrieval time, source, currency and package version under ignored `data/local/cache`. They are written atomically, reused without provider access, and never silently refreshed. Deliberately remove a specific cache file to re-download. Corrupt entries fail explicitly. New downloads can revise historical values; preserve saved bytes for exact reproduction. Public provider access does not establish redistribution rights.

All current, alternative and benchmark series use the same observed-date intersection; no filling or silent stock removal. Coverage and exclusions are disclosed, with at least 252 matching observations required. Missing/nonpositive/nonfinite quotes and duplicates fail. Dates absent from all histories remain undetectable without an independent exchange calendar. Changing the alternative can change the common period and thus current results. Foundation alignment retains stricter gap rejection.

Each series starts at 100: `I(t) = 100 × Σ[w_i × P_i(t)/P_i(t0)]`. Initial fractional weights, buy and hold, no rebalancing, cash flows, fees/taxes or slippage. Weights drift. Total return is endpoint growth, CAGR uses elapsed days/365.25, volatility is sample standard deviation of consecutive returns × sqrt(252). Max drawdown is a positive loss magnitude; chart drawdown is negative below the running peak. Annualization on irregular intersections is approximate. No strategy backtest, optimization, causal explanation or forecast is claimed.

## Interaction correctness

A shared request coordinator associates calculations/imports with the input revision and commentary with both revision and server analysis ID. Input changes abort outstanding client requests, clear commentary, mark reports stale and invalidate their ownership. Even if an aborted request still completes, its response and finalizer cannot alter the newer report or loading state. Duplicate requests are guarded. Aborting a browser request does not guarantee cancellation of server/provider computation already underway.

CSV merging canonicalizes aliases, preserves the other allocation, sets absent imported weights to zero, rejects duplicate identities and enforces ten stocks. Totals/hints identify incomplete allocations before submission without replacing server validation. Disabled alternatives have disabled editor controls and unavailable choices removed. Date inspection has a keyboard slider and pointer/touch support; responsive chart coordinates keep axis text at readable CSS dimensions.

Print/save PDF uses browser print CSS, not a service. It includes actual dates, metrics, charts, all initial allocations, any current commentary and concise assumptions. Printing is disabled when results are stale. Browser/print verification status is recorded in FINAL_POLISH.md; do not infer verification from implementation alone.

## Gemini

The working default remains **gemini-3.5-flash-lite**, using official `google-genai` 2.34.0, server-side `GEMINI_API_KEY`, optional `GEMINI_MODEL` override, a 60-second request timeout and one SDK attempt. No calls happen automatically. Free-only usage requires a confirmed eligible Free-project key and available quota; the app does not inspect billing tiers.

Server-owned reports are bounded to 32 entries and one hour. The browser supplies only the random report ID; fabricated client metrics are not trusted. Gemini receives calculated metrics/allocations, benchmark/scenario context, coverage and limitations. Each structured section contains number-free prose plus enumerated fact IDs; the server validates them and supplies the displayed values. The UI separates prose from numerical facts. Benchmark's obvious 100% allocation is omitted; section vocabularies favor relevant metrics. Flattened `sections` remain compatible; `section_details` adds separate summary and labeled facts.

Checks validate numerical sourcing, not every qualitative interpretation. Failed output is discarded. Errors expose safe categories/HTTP codes only, never keys or raw provider exceptions. Gemini output is rendered as text. Missing key, timeout, quota, access and provider failure preserve historical functionality. The [official SDK](https://googleapis.github.io/python-genai/), [structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [model/pricing](https://ai.google.dev/gemini-api/docs/pricing) and [billing](https://ai.google.dev/gemini-api/docs/billing) references explain provider behavior; no billing configuration is changed by this project.

## Measured evidence

The recorded successful live Flash-Lite comparison took **2 seconds** and passed numerical-source validation: [live evidence](evidence/gemini-live-verification.json). That artifact predates the final presentation polish. It establishes one live example, not reliability or qualitative-accuracy rates. Routine final tests use mocks, without new live calls or credential changes. Earlier 3.8 timeout/debug records describe history, not the current configured model or current success status.

Saved 739 matching observations, 2022-01-03–2024-12-31:

| Allocation | Return | CAGR | Volatility | Max drawdown |
| --- | ---: | ---: | ---: | ---: |
| Current Reliance/HDFC/Infosys 40/30/30 | 12.72% | 4.08% | 17.03% | 16.88% |
| Alternative 20/40/40 | 13.39% | 4.29% | 17.01% | 19.41% |
| NIFTY ETF | 38.67% | 11.54% | 12.57% | 15.73% |

The alternative has 0.68 percentage points higher return and 2.54 points larger maximum drawdown. These chosen retrospective outcomes do not establish investment-performance improvement. Cached TCS/Infosys 2021–2023 reproduction covers 741 dates and remains available.

Final automated suite: **64 Python checks + 5 JavaScript checks**. [Python result](evidence/dashboard-tests.txt), [async/CSV result](evidence/dashboard-ui-tests.txt), [offline dashboard reproduction](evidence/dashboard-verification.json), [offline foundation reproduction](evidence/foundation-final-verification.json). The two Python verifiers remove key variables and block network connections; the custom dashboard cache must already exist. Earlier screenshots/test artifacts are historical until explicitly replaced by final screenshots; see [final polish status](FINAL_POLISH.md).

## Credit

May–July 2025 internship collaboration: Atharva Suraj Krishnan, Kevin Felix Dcunha (`nabujika`), Omkar Shrikanth (`OmkarShr`). No strict ownership division; Kevin and Omkar wrote more original code. Forked from OmkarShr/FINANCEKVGAI; notebooks/history preserved. Restoration, validation and dashboard development are October 2026 work. No resume edits or sole-original-author claim.
