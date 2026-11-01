import hashlib
import json
import socket

import pandas as pd
import pytest

from portfolio import SYMBOLS, describe_coverage


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Tests must not access the network")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


@pytest.fixture
def snapshot(tmp_path):
    """Synthetic calculation fixture only; never used as demonstration data."""
    dates = pd.bdate_range("2022-01-03", periods=260).strftime("%Y-%m-%d")
    prices = pd.DataFrame([
        {"Date": date, "Symbol": symbol, "AdjClose": start + i / 10}
        for symbol, start in zip(SYMBOLS, (100, 200, 500))
        for i, date in enumerate(dates)
    ])
    raw = prices.to_csv(index=False).encode()
    metadata = {
        "schema_version": 1, "provider": "Yahoo Finance", "symbols": list(SYMBOLS),
        "currency": "INR", "price_field": "Adj Close", "requested_start": "2022-01-01",
        "requested_end_exclusive": "2025-01-01", "retrieved_at_utc": "2026-10-31T00:00:00+00:00",
        "yfinance_version": "synthetic-test-fixture", "sha256": hashlib.sha256(raw).hexdigest(),
        "coverage": describe_coverage(prices),
    }
    (tmp_path / "prices.csv").write_bytes(raw)
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    return tmp_path
