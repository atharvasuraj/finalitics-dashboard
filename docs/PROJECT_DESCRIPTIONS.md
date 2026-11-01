# Verified project descriptions

These are supporting-entry drafts, not edits to a resume. Keep **2025 internship team work** separate from the **2026 restoration**, and do not claim sole ownership of the original implementation.

## IT-focused

> Collaborated on a Flask-based financial-analysis prototype at KVGAI Tech with two fellow interns. In a later restoration, made one historical stock-portfolio workflow reproducible using saved data, date-aligned calculations, validated CSV uploads, explicit error handling, and automated numerical/API checks.

Short supporting-project version:

> Restored and validated a historical portfolio analyser from a collaborative internship prototype; added an offline saved-data path, buy-and-hold calculations, CSV validation, and reproducible tests.

If attaching evidence, cite the current test report and restoration date separately. Do not describe the restoration tests as internship accomplishments.

## Finance-focused

> Collaborated on an internship prototype exploring portfolio analysis and allocation. Later validated a three-stock historical example using adjusted prices, initial portfolio weights, buy-and-hold assumptions, and transparent return, volatility, and drawdown calculations.

Discussion version:

> The restoration analyses a 40/30/30 illustrative stock allocation across 739 shared observations in 2022–2024. It distinguishes adjusted stock returns from mutual-fund NAV returns and makes rebalancing, missing-data, and annualization assumptions explicit.

The observed 12.72% total return and other metrics describe the sample; they are not resume claims of improved returns or a profitable strategy.

## Claims supported by the current evidence

- One local Flask workflow loads a sample or uploaded allocation and analyses a saved Yahoo snapshot without runtime network access or a paid/LLM key.
- Price normalization, symbol/date alignment, percentage-weight validation, no-rebalancing arithmetic, calendar CAGR, volatility, and drawdown have focused checks.
- The original report and notebooks establish an exploratory team project. The inspected source does not establish a completed integrated multi-LLM finance system, benchmark-beating performance, forecasting accuracy, or functioning deployment.

## Credit and boundaries

Atharva Suraj Krishnan, Kevin Felix Dcunha (`nabujika`), and Omkar Shrikanth (`OmkarShr`) worked collaboratively during May–July 2025, without strict individual ownership boundaries. Kevin and Omkar wrote more original code, as described by Atharva. The fork originates from `OmkarShr/FINANCEKVGAI`. Attribute only the later restoration to this later work; never infer 2025 individual ownership from Git commits.

Avoid: "built the entire platform", "multi-agent production system", "improved investment returns", "accurate ARIMA forecasting", "backtested strategies", "processed hundreds of securities", or "deployed financial advisor". None is demonstrated by this restoration.

## Later dashboard expansion (October 2026)

IT-focused supporting-entry draft:

> Extended a restored team internship prototype into a Flask portfolio dashboard with cached historical NSE data, validated allocation editing/CSV ingestion, matched-date benchmark/scenario comparisons, interactive charts, and optional server-side Gemini interpretation with structured output and numerical sourcing checks and stale-response guards.

Finance-focused supporting-entry draft:

> Developed a later historical-analysis dashboard for comparing buy-and-hold stock allocations with a NIFTY ETF reference, documenting adjusted-price, common-date and rebalancing assumptions and quantifying return, volatility and drawdown trade-offs.

Keep the 2025 collaborative internship and this later development separately dated. A successful live Gemini 3.5 Flash-Lite example is recorded in gemini-live-verification.json (2 seconds); routine regression checks use mocks. The final presentation changes have not been live retested. This is LLM-assisted interpretation of calculated historical results, not forecasting, portfolio optimization or a multi-agent system. Retain the original team credit and do not attribute the team's implementation solely to Atharva. Measured scenario differences are sample outcomes, not improved investment performance.
