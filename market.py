"""Bounded NSE data retrieval/cache; calculations stay in portfolio.py."""
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re

import pandas as pd
from portfolio import InputError, DataError, align_prices

BENCHMARK = 'NIFTYBEES.NS'


def symbol(value):
    value = str(value).strip().upper()
    if not value.endswith('.NS'):
        value += '.NS'
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9&-]{0,24}\.NS', value):
        raise InputError('Use NSE symbols such as TCS.NS; only INR/NSE stocks are supported.')
    return value


def date_range(start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError) as exc:
        raise InputError('Use valid YYYY-MM-DD start and end dates.') from exc
    if first >= last or last >= date.today() or (last-first).days > 3653:
        raise InputError('Choose an increasing historical range ending before today, at most 10 years long. End date is inclusive.')
    return first, last


def history(ticker, start, end, cache: Path, allow_fetch=True):
    """Immutable cache per exact request; corrupt entries fail, never silently refresh."""
    key = hashlib.sha256(f'{ticker}:{start}:{end}:adjusted-v1'.encode()).hexdigest()
    path = cache / (key + '.json')
    if path.exists():
        try:
            record = json.loads(path.read_text())
            raw = record['csv'].encode()
            if hashlib.sha256(raw).hexdigest() != record['metadata']['sha256']:
                raise ValueError('checksum')
            if record['metadata']['request'] != [ticker, start, end]:
                raise ValueError('request')
            frame = pd.read_csv(io.BytesIO(raw), dtype={'AdjClose': str})
            frame['AdjClose'] = frame['AdjClose'].astype(float)
            align_prices(frame, [ticker])
            return frame, {**record['metadata'], 'cache_hit': True}
        except (ValueError, KeyError, OSError) as exc:
            raise DataError(f'{ticker}: cache is corrupt; remove {path.name} from the cache and retrieve again.') from exc
    if not allow_fetch:
        raise DataError(f'{ticker}: saved benchmark cache is missing. Run python scripts/prepare_dashboard.py once online.')
    try:
        import yfinance as yf
        cache.mkdir(parents=True, exist_ok=True)
        yf.set_tz_cache_location(str(cache / 'provider'))
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=(date.fromisoformat(end)+pd.Timedelta(days=1)).isoformat(), interval='1d',
                             auto_adjust=False, back_adjust=False, repair=False, keepna=True, actions=True, timeout=20)
        info = stock.get_history_metadata()
        if hist.empty or 'Adj Close' not in hist:
            raise DataError(f'{ticker}: unsupported symbol or no historical data for this range.')
        if info.get('currency') != 'INR' or info.get('exchangeTimezoneName') != 'Asia/Kolkata':
            raise DataError(f'{ticker}: only INR securities on the NSE exchange timezone are supported.')
        frame = pd.DataFrame({'Date':hist.index.tz_convert('Asia/Kolkata').strftime('%Y-%m-%d'),
                              'Symbol':ticker,'AdjClose':hist['Adj Close'].to_numpy()})
        align_prices(frame, [ticker])
        raw = frame.to_csv(index=False, float_format='%.17g').encode()
        metadata = {'request':[ticker,start,end], 'currency':'INR','provider':'Yahoo Finance','price_field':'Adj Close',
                    'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'yfinance_version':yf.__version__,
                    'sha256':hashlib.sha256(raw).hexdigest()}
        # One atomic file holds both observations and metadata.
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode='w',dir=cache,delete=False) as handle:
            json.dump({'metadata':metadata,'csv':raw.decode()},handle)
            temporary = handle.name
        os.replace(temporary,path)
        return frame, {**metadata,'cache_hit':False}
    except DataError:
        raise
    except Exception as exc:
        raise DataError(f'{ticker}: historical retrieval failed. Check symbol, coverage, connectivity or provider limits; cached and saved examples remain available.') from exc
