"""Offline historical stock analysis; no data-provider or LLM imports."""

import csv
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("RELIANCE.NS", "HDFCBANK.NS", "INFY.NS")
WEIGHT_TOLERANCE = 0.01  # percentage points; permits 33.33/33.33/33.33
MIN_OBSERVATIONS = 252
ASSUMPTIONS = [
    "Initial allocation, then buy and hold with no rebalancing; weights drift over time.",
    "Fractional holdings; no contributions, withdrawals, fees, taxes, or slippage.",
    "Adjusted stock prices provide a dividend/split-adjusted return proxy, not a cash-account reconstruction or mutual-fund NAV.",
    "Portfolio index starts at 100; it is not a rupee balance.",
    "Volatility uses sample daily-return standard deviation and 252 observations per year; CAGR uses elapsed calendar days / 365.25.",
    "Illustrative stocks and dates; historical returns do not establish a profitable strategy or predict future returns.",
]


class InputError(ValueError):
    """A portfolio upload cannot be interpreted as a valid allocation."""


class DataError(ValueError):
    """The local snapshot cannot support the requested calculation."""


def parse_portfolio(raw: bytes, allowed_symbols=SYMBOLS, max_rows=3) -> pd.Series:
    """Read percentage weights. Preserve allocation intent; tolerate rounding only."""
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Upload a valid UTF-8 CSV with Symbol,Weight columns.") from exc
    if not rows or [s.strip() for s in rows[0]] != ["Symbol", "Weight"]:
        raise InputError("CSV must have exactly Symbol,Weight columns, in that order.")
    if not 1 <= len(rows) - 1 <= max_rows:
        raise InputError(f"Provide 1 to {max_rows} stock rows with percentage weights summing to 100.")
    weights = {}
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise InputError(f"Row {number} must have exactly two fields.")
        symbol = row[0].strip().upper()
        if symbol and not symbol.endswith(".NS"):
            symbol += ".NS"
        if symbol not in allowed_symbols:
            raise InputError(f"Row {number}: unsupported symbol. Use {', '.join(allowed_symbols)}.")
        if symbol in weights:
            raise InputError(f"Row {number}: duplicate symbol {symbol}.")
        try:
            weight = float(row[1])
        except ValueError as exc:
            raise InputError(f"Row {number}: Weight must be a number in percentage points.") from exc
        if not math.isfinite(weight) or weight < 0 or weight > 100 + WEIGHT_TOLERANCE:
            raise InputError(f"Row {number}: Weight must be a finite percentage between 0 and 100 (plus rounding tolerance).")
        weights[symbol] = weight
    total = math.fsum(weights.values())
    if total <= 0 or abs(total - 100) > WEIGHT_TOLERANCE + 1e-10:
        raise InputError(f"Weights sum to {total:g}%; expected 100% (tolerance 0.01 percentage points).")
    # The sole normalization is the explicitly documented rounding correction.
    return pd.Series({s: weights[s] / total for s in sorted(weights)}, dtype=float)


def align_prices(prices: pd.DataFrame, symbols, min_observations=MIN_OBSERVATIONS) -> pd.DataFrame:
    """Align dated long-form prices, allowing boundary trimming but no internal gaps."""
    if list(prices.columns) != ["Date", "Symbol", "AdjClose"]:
        raise DataError("Snapshot must have Date,Symbol,AdjClose columns.")
    selected = prices[prices["Symbol"].isin(symbols)].copy()
    if set(selected["Symbol"]) != set(symbols):
        raise DataError("Snapshot is missing a requested stock; no stock was dropped.")
    try:
        selected["Date"] = pd.to_datetime(selected["Date"], format="%Y-%m-%d", errors="raise")
        selected["AdjClose"] = pd.to_numeric(selected["AdjClose"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise DataError("Snapshot contains invalid dates or prices.") from exc
    if selected["Date"].isna().any() or selected.duplicated(["Date", "Symbol"]).any():
        raise DataError("Snapshot has missing or duplicate stock dates.")
    if not np.isfinite(selected["AdjClose"].to_numpy(dtype=float)).all() or (selected["AdjClose"] <= 0).any():
        raise DataError("Snapshot prices must be finite, positive, and present.")
    groups = selected.groupby("Symbol")["Date"]
    first, last = groups.min().max(), groups.max().min()
    if first >= last:
        raise DataError("Stocks have no overlapping historical period.")
    selected = selected[selected["Date"].between(first, last)]
    wide = selected.pivot(index="Date", columns="Symbol", values="AdjClose").sort_index()
    if wide.isna().any().any():
        raise DataError("Stock trading dates differ inside the common period. No prices were filled or skipped.")
    if len(wide) < min_observations:
        raise DataError(f"Need at least {min_observations} common observations; found {len(wide)}.")
    return wide.loc[:, sorted(symbols)]


def load_snapshot(directory: Path) -> tuple[pd.DataFrame, dict]:
    """Verify snapshot provenance and byte checksum before using any observations."""
    try:
        raw = (directory / "prices.csv").read_bytes()
        metadata = json.loads((directory / "metadata.json").read_text())
    except (OSError, ValueError) as exc:
        raise DataError("Saved data is missing or unreadable. Run: python scripts/prepare_data.py") from exc
    required = {"schema_version", "provider", "symbols", "currency", "price_field", "requested_start", "requested_end_exclusive", "retrieved_at_utc", "yfinance_version", "sha256", "coverage"}
    if not isinstance(metadata, dict) or not required.issubset(metadata):
        raise DataError("Snapshot metadata is incomplete. Prepare the data again.")
    if (metadata["schema_version"] != 1 or metadata["symbols"] != list(SYMBOLS)
            or metadata["provider"] != "Yahoo Finance" or metadata["currency"] != "INR"
            or metadata["price_field"] != "Adj Close"
            or metadata["requested_start"] != "2022-01-01"
            or metadata["requested_end_exclusive"] != "2025-01-01"):
        raise DataError("Snapshot metadata does not describe the supported 2022–2024 adjusted-stock dataset.")
    if hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
        raise DataError("Saved data checksum mismatch. Restore the recorded snapshot or prepare it again.")
    try:
        prices = pd.read_csv(io.BytesIO(raw))
        if set(prices["Symbol"]) != set(SYMBOLS):
            raise DataError("Snapshot must contain exactly the three supported stocks.")
        # Validate the entire snapshot even when an upload uses a subset.
        align_prices(prices, SYMBOLS)
        all_dates = pd.to_datetime(prices["Date"], format="%Y-%m-%d", errors="raise")
        if (all_dates.min() < pd.Timestamp("2022-01-01")
                or all_dates.max() >= pd.Timestamp("2025-01-01")):
            raise DataError("Snapshot dates are outside the documented period.")
        if metadata["coverage"] != describe_coverage(prices):
            raise DataError("Snapshot coverage does not match its metadata.")
    except (ValueError, TypeError, KeyError, pd.errors.ParserError) as exc:
        if isinstance(exc, DataError):
            raise
        raise DataError("Saved price data is malformed. Prepare it again.") from exc
    return prices, metadata


def describe_coverage(prices: pd.DataFrame) -> dict:
    return {
        symbol: {"start": str(group["Date"].min()), "end": str(group["Date"].max()), "observations": len(group)}
        for symbol, group in prices.groupby("Symbol")
    }


def calculate_portfolio(prices: pd.DataFrame, weights: pd.Series) -> tuple[pd.Series, dict]:
    """Buy-and-hold adjusted-price index. Inputs already validated and date aligned."""
    weights = weights.reindex(prices.columns)
    if weights.isna().any() or not np.isfinite(weights).all() or (weights < 0).any() or not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0):
        raise InputError("Calculation requires aligned, nonnegative weights summing to one.")
    index = prices.div(prices.iloc[0]).mul(weights, axis="columns").sum(axis=1) * 100
    returns = index.pct_change(fill_method=None).iloc[1:]
    years = (index.index[-1] - index.index[0]).days / 365.25
    total_return = float(index.iloc[-1] / index.iloc[0] - 1)
    metrics = {
        "total_return": total_return,
        "cagr": float((1 + total_return) ** (1 / years) - 1),
        "annualized_volatility": float(returns.std(ddof=1) * np.sqrt(252)),
        "max_drawdown": float((1 - index / index.cummax()).max()),
    }
    if not np.isfinite(index).all() or not all(math.isfinite(v) for v in metrics.values()):
        raise DataError("These observations cannot produce finite portfolio metrics.")
    return index, metrics


def analyse(raw: bytes, directory: Path) -> dict:
    weights = parse_portfolio(raw)
    prices, metadata = load_snapshot(directory)
    aligned = align_prices(prices, weights.index)
    index, metrics = calculate_portfolio(aligned, weights)
    return {
        "metrics": metrics,
        "allocations": [{"symbol": s, "weight_percent": float(w * 100)} for s, w in weights.items()],
        "series": [{"date": date.strftime("%Y-%m-%d"), "index": float(value)} for date, value in index.items()],
        "period": {"start": index.index[0].strftime("%Y-%m-%d"), "end": index.index[-1].strftime("%Y-%m-%d"), "observations": len(index)},
        "dataset": metadata,
        "assumptions": ASSUMPTIONS,
    }
