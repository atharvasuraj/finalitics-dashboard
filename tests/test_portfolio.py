import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from portfolio import (DataError, InputError, SYMBOLS, align_prices, analyse,
                       calculate_portfolio, load_snapshot, parse_portfolio)


def long_prices(rows):
    wide = pd.DataFrame(rows, index=pd.date_range("2022-01-03", periods=3))
    wide.index.name = "Date"
    return wide.reset_index().melt("Date", var_name="Symbol", value_name="AdjClose").assign(
        Date=lambda frame: frame.Date.dt.strftime("%Y-%m-%d")
    )


def test_hand_calculation_and_buy_hold_not_daily_rebalancing():
    # Unequal share prices, equal starting capital. First stock doubles then halves.
    # Buy/hold: 100 -> 150 -> 100. Daily 50/50 rebalancing ends at 112.5 instead.
    prices = align_prices(long_prices({"RELIANCE.NS": [10, 20, 10], "INFY.NS": [100, 100, 100]}),
                          ["INFY.NS", "RELIANCE.NS"], min_observations=3)
    weights = parse_portfolio(b"Symbol,Weight\nRELIANCE,50\nINFY,50\n")
    index, metrics = calculate_portfolio(prices, weights)
    assert index.tolist() == pytest.approx([100, 150, 100])
    assert index.iloc[-1] != 112.5
    assert metrics["total_return"] == pytest.approx(0)
    assert metrics["max_drawdown"] == pytest.approx(1 / 3)
    assert metrics["annualized_volatility"] == pytest.approx(np.std([.5, -1/3], ddof=1) * np.sqrt(252))


def test_calendar_cagr_and_constant_prices():
    dates = pd.to_datetime(["2022-01-03", "2022-07-04", "2023-01-03"])
    prices = pd.DataFrame({"INFY.NS": [100, 105, 110]}, index=dates)
    _, metrics = calculate_portfolio(prices, pd.Series({"INFY.NS": 1.0}))
    assert metrics["cagr"] == pytest.approx(1.1 ** (365.25/365) - 1)
    _, metrics = calculate_portfolio(prices * 0 + 17, pd.Series({"INFY.NS": 1.0}))
    assert metrics == {"total_return": 0, "cagr": 0, "annualized_volatility": 0, "max_drawdown": 0}


def test_row_and_column_order_invariance():
    raw = long_prices({"RELIANCE.NS": [10, 12, 13], "INFY.NS": [100, 90, 95]})
    prices = align_prices(raw, ["RELIANCE.NS", "INFY.NS"], min_observations=3)
    first = calculate_portfolio(prices, parse_portfolio(b"Symbol,Weight\nRELIANCE,40\nINFY,60\n"))
    reordered = calculate_portfolio(prices.iloc[::-1].sort_index().loc[:, ["RELIANCE.NS", "INFY.NS"]],
                                    parse_portfolio(b"Symbol,Weight\nINFY,60\nRELIANCE,40\n"))
    pd.testing.assert_series_equal(first[0], reordered[0])
    assert first[1] == reordered[1]
    pd.testing.assert_frame_equal(prices, align_prices(raw.iloc[::-1], ["INFY.NS", "RELIANCE.NS"], min_observations=3))


def test_rounding_tolerance_and_aliases_are_explicit():
    weights = parse_portfolio(b"\xef\xbb\xbfSymbol,Weight\n reliance ,33.33\nHDFCBANK.NS,33.33\nINFY,33.33\n")
    assert sorted(weights.index) == sorted(SYMBOLS)
    assert weights.sum() == pytest.approx(1)
    assert weights.tolist() == pytest.approx([1/3]*3)


@pytest.mark.parametrize("raw", [
    b"", b"Symbol,Weight\n", b"Stock,Weight\nINFY,100\n", b"Symbol,Weight,Extra\nINFY,100,x\n",
    b"Symbol,Weight\nINFY,100,extra\n", b'Symbol,Weight\n"INFY,100\n',
    b"Symbol,Weight\nINFY,no\n", b"Symbol,Weight\nINFY,nan\n", b"Symbol,Weight\nINFY,inf\n",
    b"Symbol,Weight\nINFY,-20\nRELIANCE,120\n", b"Symbol,Weight\nINFY,0\n",
    b"Symbol,Weight\nINFY,80\n", b"Symbol,Weight\nINFY,1\n",
    b"Symbol,Weight\nINFY,1e308\nRELIANCE,1e308\n",
    b"Symbol,Weight\nINFY,50\ninfy.ns,50\n", b"Symbol,Weight\nMSFT,100\n",
    b"Symbol,Weight\n,100\n", b"Symbol,Weight\nINFY,100\xff\n",
])
def test_invalid_uploads_rejected(raw):
    with pytest.raises(InputError):
        parse_portfolio(raw)


@pytest.mark.parametrize("problem", ["gap", "missing", "zero", "negative", "infinite", "duplicate", "stock", "date", "short"])
def test_invalid_price_data_rejected(problem):
    prices = long_prices({"RELIANCE.NS": [10, 12, 13], "INFY.NS": [100, 90, 95]})
    if problem == "gap": prices = prices.drop(1)
    if problem == "missing": prices.loc[1, "AdjClose"] = np.nan
    if problem == "zero": prices.loc[1, "AdjClose"] = 0
    if problem == "negative": prices.loc[1, "AdjClose"] = -1
    if problem == "infinite": prices["AdjClose"] = prices["AdjClose"].astype(float); prices.loc[1, "AdjClose"] = np.inf
    if problem == "duplicate": prices = pd.concat([prices, prices.iloc[[0]]])
    if problem == "stock": prices = prices[prices.Symbol != "INFY.NS"]
    if problem == "date": prices.loc[1, "Date"] = "invalid"
    with pytest.raises(DataError):
        align_prices(prices, ["RELIANCE.NS", "INFY.NS"], min_observations=252 if problem == "short" else 3)


def test_common_boundary_trim_without_filling():
    prices = long_prices({"RELIANCE.NS": [10, 12, 13], "INFY.NS": [100, 90, 95]})
    trimmed = align_prices(prices.drop(0), ["RELIANCE.NS", "INFY.NS"], min_observations=2)
    assert list(trimmed.index.strftime("%Y-%m-%d")) == ["2022-01-04", "2022-01-05"]
    assert trimmed["INFY.NS"].tolist() == [90, 95]


def test_missing_corrupt_and_mismatched_metadata(snapshot):
    prices, metadata = load_snapshot(snapshot)
    assert len(prices) == 780
    path = snapshot / "prices.csv"
    raw = path.read_bytes()
    path.write_bytes(raw + b"\n")
    with pytest.raises(DataError, match="checksum"):
        load_snapshot(snapshot)
    path.write_bytes(raw)
    metadata["coverage"]["INFY.NS"]["observations"] = 1
    (snapshot / "metadata.json").write_text(json.dumps(metadata))
    with pytest.raises(DataError, match="coverage"):
        load_snapshot(snapshot)
    path.unlink()
    with pytest.raises(DataError, match="missing"):
        load_snapshot(snapshot)


def test_corrupt_snapshot_with_matching_checksum_is_still_rejected(snapshot):
    path = snapshot / "prices.csv"
    raw = b"Wrong,Columns\n1,2\n"
    path.write_bytes(raw)
    metadata_path = snapshot / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["sha256"] = hashlib.sha256(raw).hexdigest()
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(DataError, match="malformed"):
        load_snapshot(snapshot)


def test_analysis_returns_dated_finite_results(snapshot):
    result = analyse(b"Symbol,Weight\nINFY,100\n", snapshot)
    assert result["period"]["observations"] == 260
    assert result["series"][0] == {"date": "2022-01-03", "index": 100.0}
    assert result["series"][-1]["index"] == pytest.approx(105.18)
    assert all(np.isfinite(list(result["metrics"].values())))
