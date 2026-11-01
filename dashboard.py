"""Same-period buy-and-hold comparisons, using the corrected calculation engine."""
import io
import csv
import numpy as np
import pandas as pd
from portfolio import InputError, DataError, parse_portfolio, load_snapshot, calculate_portfolio, ASSUMPTIONS
from market import symbol, date_range, history, BENCHMARK


def allocation(rows):
    if not isinstance(rows,list) or not 1 <= len(rows) <= 10:
        raise InputError('Provide 1–10 stock rows for each allocation.')
    pairs = []
    for row in rows:
        if not isinstance(row,dict) or set(row) != {'symbol','weight'}:
            raise InputError('Each row needs symbol and weight.')
        pairs.append((symbol(row['symbol']),row['weight']))
    # Reuse existing CSV weight validation, with an explicit bounded universe.
    stream=io.StringIO(); writer=csv.writer(stream); writer.writerow(['Symbol','Weight']);writer.writerows(pairs)
    return parse_portfolio(stream.getvalue().encode(), allowed_symbols=tuple(s for s,_ in pairs), max_rows=10)


def csv_allocation(raw):
    try:
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),strict=True)
        if reader.fieldnames != ['Symbol','Weight']:
            raise InputError('CSV must have Symbol,Weight columns.')
        rows=[]
        for row in reader:
            if set(row) != {'Symbol','Weight'} or None in row.values():
                raise InputError('Malformed CSV row.')
            rows.append({'symbol':row['Symbol'],'weight':row['Weight']})
        weights=allocation(rows)
        return [{'symbol':s,'weight':float(w*100)} for s,w in weights.items()]
    except (UnicodeError,csv.Error) as exc:
        raise InputError('Upload a valid UTF-8 allocation CSV.') from exc


def comparison(frames, allocations, metadata):
    """Intersect observed dates explicitly; disclose dropped dates, never fill prices."""
    merged=pd.concat(frames,ignore_index=True)
    if merged.duplicated(['Date','Symbol']).any():
        raise DataError('Duplicate stock dates in comparison data.')
    wide=merged.pivot(index='Date',columns='Symbol',values='AdjClose').sort_index()
    values=wide.to_numpy(dtype=float)
    if np.isinf(values).any() or (wide <= 0).any().any():
        raise DataError('Prices must be positive and finite.')
    # A missing quote on a supplied date is rejected; differing valid calendars
    # are intersected below rather than treating a missing quote as a price.
    if merged.AdjClose.isna().any():
        raise DataError('Provider returned missing prices; no filling is performed.')
    coverage={s:{'start':str(g.Date.min()),'end':str(g.Date.max()),'observations':len(g)} for s,g in merged.groupby('Symbol')}
    common=wide.dropna()
    if len(common)<252:
        raise DataError(f'Only {len(common)} matching dates across portfolio, alternative and benchmark; at least 252 required.')
    common.index=pd.to_datetime(common.index,format='%Y-%m-%d')
    output={}
    for name, weights in allocations.items():
        selected=common.loc[:,weights.index]
        index, metrics=calculate_portfolio(selected,weights)
        output[name]={'metrics':metrics,'allocations':[{'symbol':s,'weight_percent':float(w*100)} for s,w in weights.items()],
                      'index':index.tolist(),'drawdown':(100*(index/index.cummax()-1)).tolist()}
    return {'portfolios':output,'dates':common.index.strftime('%Y-%m-%d').tolist(),
            'period':{'start':common.index[0].strftime('%Y-%m-%d'),'end':common.index[-1].strftime('%Y-%m-%d'),'observations':len(common)},
            'coverage':coverage,'excluded_dates':{s:int(len(g)-len(common)) for s,g in merged.groupby('Symbol')},
            'dataset':metadata,'assumptions':ASSUMPTIONS+['All comparisons use the intersection of observed dates across every selected stock and benchmark; exclusions are disclosed. No currency conversion.',
            'NIFTYBEES.NS is an investable NIFTY ETF adjusted-price proxy, including fund fees/tracking effects; not the official NIFTY total-return index.']}


def build(payload, data_dir, cache):
    if not isinstance(payload,dict):
        raise InputError('Expected a JSON object.')
    current=allocation(payload.get('current'))
    alt=allocation(payload['alternative']) if payload.get('alternative') else None
    if payload.get('source','saved') not in ('saved','historical'):
        raise InputError('Choose saved or historical data.')
    saved=payload.get('source','saved')=='saved'
    start,end=payload.get('start','2022-01-01'),payload.get('end','2024-12-31')
    date_range(start,end)
    allocations={'current':current}
    if alt is not None: allocations['alternative']=alt
    allocations['benchmark']=pd.Series({BENCHMARK:1.0})
    symbols=sorted(set().union(*(set(w.index) for w in allocations.values())))
    if len(set(symbols)-{BENCHMARK}) > 10:
        raise InputError('Use at most ten distinct stocks across both allocations.')
    frames=[];metadata={}
    original,manifest=load_snapshot(data_dir) if saved else (None,None)
    if saved and (start,end)!=('2022-01-01','2024-12-31'):
        raise InputError('Saved example uses 2022–2024. Choose historical retrieval for custom dates.')
    for ticker in symbols:
        if saved and ticker in manifest['symbols']:
            frames.append(original[original.Symbol==ticker]);metadata[ticker]=manifest
        else:
            if saved and ticker!=BENCHMARK:
                raise InputError('This stock is outside the saved example. Choose historical retrieval.')
            frame,meta=history(ticker,start,end,cache,allow_fetch=not saved)
            frames.append(frame);metadata[ticker]=meta
    result=comparison(frames,allocations,metadata)
    result['requested']={'start':start,'end':end,'source':'saved' if saved else 'historical'}
    return result
