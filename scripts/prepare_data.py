#!/usr/bin/env python3
"""One-time Yahoo download for the local demo. Never imported by the Flask app."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio import DataError, SYMBOLS, align_prices, describe_coverage

ROOT = Path(__file__).resolve().parents[1]


def prepare(directory: Path, replace=False):
    import pandas as pd
    import yfinance as yf

    if not replace and any((directory / name).exists() for name in ("prices.csv", "metadata.json")):
        raise DataError("A snapshot already exists. Preserve it for reproducibility, or use --replace explicitly.")
    # Keep yfinance's SQLite cache local, outside the source tree.
    directory.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(directory / "yfinance-cache"))
    frames = []
    for symbol in SYMBOLS:
        print(f"Fetching {symbol}: 2022-01-01 through 2024-12-31", flush=True)
        ticker = yf.Ticker(symbol)
        hist = ticker.history(
            start="2022-01-01", end="2025-01-01", interval="1d",
            auto_adjust=False, back_adjust=False, actions=True, repair=False,
            keepna=True, rounding=False, prepost=False, timeout=30, raise_errors=True,
        )
        if hist.empty or "Adj Close" not in hist:
            raise DataError(f"{symbol}: provider returned no adjusted closing prices.")
        info = ticker.get_history_metadata()
        if info.get("currency") != "INR" or info.get("exchangeTimezoneName") != "Asia/Kolkata":
            raise DataError(f"{symbol}: expected INR stock prices dated in Asia/Kolkata.")
        # Preserve the exchange-local calendar date; do not convert midnight to UTC.
        dates = hist.index.tz_convert("Asia/Kolkata").strftime("%Y-%m-%d")
        frames.append(pd.DataFrame({"Date": dates, "Symbol": symbol, "AdjClose": hist["Adj Close"].to_numpy()}))
    prices = pd.concat(frames, ignore_index=True).sort_values(["Symbol", "Date"])
    align_prices(prices, SYMBOLS)  # No dropping observations, filling gaps, or substituting data.
    if prices["Date"].min() < "2022-01-01" or prices["Date"].max() >= "2025-01-01":
        raise DataError("Provider returned observations outside the requested dates.")
    raw = prices.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")
    metadata = {
        "schema_version": 1,
        "provider": "Yahoo Finance",
        "source_url": "https://finance.yahoo.com/",
        "symbols": list(SYMBOLS),
        "currency": "INR",
        "exchange_timezone": "Asia/Kolkata",
        "price_field": "Adj Close",
        "adjustment": "Provider dividend/split-adjusted closing-price return proxy; no additional adjustment or dividend cash flows added.",
        "requested_start": "2022-01-01",
        "requested_end_exclusive": "2025-01-01",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "yfinance_version": yf.__version__,
        "parameters": {"interval": "1d", "auto_adjust": False, "back_adjust": False, "actions": True, "repair": False, "keepna": True, "rounding": False, "prepost": False},
        "coverage": describe_coverage(prices),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    # Write only after all stocks pass validation. Replacing either file is atomic;
    # an interruption between replacements is detected by the loader's checksum.
    for name, contents in (("prices.csv", raw), ("metadata.json", (json.dumps(metadata, indent=2) + "\n").encode())):
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
            handle.write(contents)
            temporary = handle.name
        os.replace(temporary, directory / name)
    print(json.dumps(metadata, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/local")
    parser.add_argument("--replace", action="store_true", help="Explicitly replace an existing snapshot; results/checksum may change.")
    args = parser.parse_args()
    try:
        prepare(args.output, args.replace)
    except Exception as exc:
        parser.exit(1, f"Data preparation failed: {exc}\nNo synthetic fallback is available. Check provider availability and rerun.\n")


if __name__ == "__main__":
    main()
