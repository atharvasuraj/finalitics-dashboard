import json
from pathlib import Path
import pandas as pd
import pytest
from dashboard import allocation,comparison,build,csv_allocation
from portfolio import InputError,DataError
from market import history,date_range,symbol
from interpretation import facts_for,validate_response,interpret


def frames():
    dates=pd.bdate_range('2022-01-03',periods=260).strftime('%Y-%m-%d')
    return [pd.DataFrame({'Date':dates,'Symbol':s,'AdjClose':[start+i for i in range(260)]}) for s,start in [('TCS.NS',100),('INFY.NS',200),('NIFTYBEES.NS',300)]]


def test_shared_dates_and_weighted_terminal_calculation():
    f=frames(); f[2]=f[2].iloc[3:]
    a=allocation([{'symbol':'TCS','weight':60},{'symbol':'INFY','weight':40}])
    b=allocation([{'symbol':'TCS','weight':40},{'symbol':'INFY','weight':60}])
    r=comparison(f,{'current':a,'alternative':b,'benchmark':pd.Series({'NIFTYBEES.NS':1})},{})
    assert r['period']['observations']==257
    assert r['excluded_dates']['TCS.NS']==3
    assert all(len(p['index'])==257 for p in r['portfolios'].values())
    assert r['portfolios']['current']['index'][-1]==pytest.approx(100*(.6*359/103+.4*459/203))
    same=comparison(f,{'current':a,'alternative':a},{})
    assert same['portfolios']['current']==same['portfolios']['alternative']


def test_gaps_disclosed_but_missing_quotes_rejected():
    f=frames();f[1]=f[1].drop(40)
    r=comparison(f,{'current':pd.Series({'TCS.NS':1})},{})
    assert r['period']['observations']==259
    assert r['excluded_dates']['TCS.NS']==1
    f[0].loc[4,'AdjClose']=float('nan')
    with pytest.raises(DataError):comparison(f,{'current':pd.Series({'TCS.NS':1})},{})


def test_general_validation():
    assert csv_allocation(b'Symbol,Weight\nTCS,100\n')[0]['symbol']=='TCS.NS'
    for rows in ([{'symbol':'TCS','weight':40}], [{'symbol':'TCS','weight':50},{'symbol':'TCS.NS','weight':50}], [{'symbol':'MSFT.US','weight':100}]):
        with pytest.raises(InputError):allocation(rows)
    with pytest.raises(InputError):date_range('2024-12-31','2022-01-01')
    with pytest.raises(InputError):date_range('x','y')
    with pytest.raises(DataError):history('TCS.NS','2022-01-01','2024-12-31',Path('/nonexistent'),allow_fetch=False)


def test_cache_checks_integrity_and_skips_network(tmp_path):
    import hashlib
    raw=frames()[0].to_csv(index=False)
    key=hashlib.sha256(b'TCS.NS:2022-01-01:2024-12-31:adjusted-v1').hexdigest()
    meta={'sha256':hashlib.sha256(raw.encode()).hexdigest(),'request':['TCS.NS','2022-01-01','2024-12-31']}
    path=tmp_path/(key+'.json');path.write_text(json.dumps({'csv':raw,'metadata':meta}))
    assert history('TCS.NS','2022-01-01','2024-12-31',tmp_path)[1]['cache_hit']
    path.write_text('{}')
    with pytest.raises(DataError):history('TCS.NS','2022-01-01','2024-12-31',tmp_path)


def test_commentary_numerical_validation_and_fallback(monkeypatch):
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    facts=facts_for(r)
    valid={s:'The observed return was {{current.total_return}} over this historical period.' for s in ('performance','risk','comparison')}
    assert '%' in validate_response(json.dumps(valid),facts)['performance']
    for text in ['It returned 500%.','It doubled in value.','Return {{invented.return}}.']:
        with pytest.raises(ValueError):validate_response(json.dumps({**valid,'risk':text}),facts)
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    assert interpret(r)['status']=='unavailable'


def test_api_uses_server_report_and_unknown_ids_rejected(snapshot,monkeypatch):
    from app import create_app
    import dashboard
    fake=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    monkeypatch.setattr(dashboard,'build',lambda *args:fake)
    # create_app imports build after monkeypatching
    client=create_app({'TESTING':True,'DATA_DIR':snapshot}).test_client()
    r=client.post('/dashboard/analyse',json={})
    assert r.status_code==200
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    assert client.post('/dashboard/interpret',json={'analysis_id':r.json['analysis_id']}).json['status']=='unavailable'
    assert client.post('/dashboard/interpret',json={'analysis_id':'unknown','metrics':{'return':999}}).status_code==400


def test_sdk_structured_success_and_provider_failure(monkeypatch):
    from google import genai
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    class Client:
        def __init__(self,**kwargs):self.models=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def generate_content(self,**kwargs):
            assert kwargs['config'].response_mime_type=='application/json'
            assert 'allocations' in kwargs['contents']
            return type('Response',(),{'text':json.dumps({s:'Historical return was {{current.total_return}}; future returns remain unknown.' for s in ('performance','risk','comparison')})})()
    monkeypatch.setenv('GEMINI_API_KEY','test-not-a-real-key')
    monkeypatch.setattr(genai,'Client',Client)
    assert interpret(r)['status']=='ready'
    class Failed(Client):
        def generate_content(self,**kwargs):raise RuntimeError('test-secret-never-expose')
    monkeypatch.setattr(genai,'Client',Failed)
    result=interpret(r)
    assert result['status']=='unavailable'
    assert 'test-secret' not in json.dumps(result)


def test_short_comparison_and_duplicate_dates_fail():
    f=[frame.iloc[:30] for frame in frames()]
    with pytest.raises(DataError,match='252'):comparison(f,{'current':pd.Series({'TCS.NS':1})},{})
    f=frames();f[0]=pd.concat([f[0],f[0].iloc[[0]]])
    with pytest.raises(DataError,match='Duplicate'):comparison(f,{'current':pd.Series({'TCS.NS':1})},{})


@pytest.mark.parametrize('code,expected',[(400,'request_rejected'),(401,'authentication_or_access'),(403,'authentication_or_access'),(404,'model_unavailable'),(429,'quota_or_rate_limit'),(503,'provider_unavailable'),(504,'request_timeout')])
def test_gemini_errors_expose_only_safe_category(monkeypatch,code,expected):
    from google import genai
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    class Failure(Exception):pass
    error=Failure('secret-key-and-provider-response-must-not-appear')
    error.code=code
    class Client:
        def __init__(self,**kwargs):self.models=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def generate_content(self,**kwargs):raise error
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    monkeypatch.setattr(genai,'Client',Client)
    result=interpret(r)
    assert result['reason']==expected
    assert result['http_status']==code
    assert 'secret-key' not in json.dumps(result)
    assert 'private-test-key' not in json.dumps(result)


def test_gemini_validation_failure_is_distinct(monkeypatch):
    from google import genai
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    class Client:
        def __init__(self,**kwargs):self.models=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def generate_content(self,**kwargs):return type('Response',(),{'text':'{}'})()
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    monkeypatch.setattr(genai,'Client',Client)
    assert interpret(r)['reason']=='response_validation'


def test_gemini_timeout_budget_and_transport_failure(monkeypatch):
    from google import genai
    import httpx
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    class Client:
        def __init__(self,**kwargs):
            assert kwargs['http_options'].timeout == 60000
            assert kwargs['http_options'].retry_options.attempts == 1
            self.models=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def generate_content(self,**kwargs):
            assert kwargs['config'].temperature is None
            raise httpx.ReadTimeout('secret-request-url-must-not-appear')
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    monkeypatch.setattr(genai,'Client',Client)
    result=interpret(r)
    assert result['reason']=='request_timeout'
    assert 'secret-request-url' not in json.dumps(result)


def test_diagnostic_does_not_send_without_key(monkeypatch,capsys):
    from scripts.check_gemini import run, safe_error
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    assert run()==1
    assert 'No requests sent' in capsys.readouterr().out
    error=RuntimeError('private-key-and-provider-body')
    error.code=504
    result=safe_error(error)
    assert result['kind']=='timeout'
    assert 'private-key' not in json.dumps(result)


def test_enum_fact_sections_render_only_server_numbers():
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1})},{})
    facts=facts_for(r)
    section={'summary':'The historical result describes this allocation and does not predict future performance.', 'fact_ids':['current.total_return','current.max_drawdown']}
    raw={topic:section for topic in ('performance','risk','comparison')}
    result=validate_response(json.dumps(raw),facts)
    assert facts['current.total_return'] in result['performance']
    for invalid in [
        {**section,'fact_ids':['benchmark.1']},
        {**section,'summary':'The portfolio returned 500%.'},
        {**section,'summary':'It returned {{current.total_return}}.'},
        {**section,'fact_ids':[]},
    ]:
        with pytest.raises(ValueError):
            validate_response(json.dumps({**raw,'risk':invalid}),facts)


def test_structured_commentary_has_separate_facts_and_relevant_schema(monkeypatch):
    from google import genai
    r=comparison(frames(),{'current':pd.Series({'TCS.NS':1}),'benchmark':pd.Series({'NIFTYBEES.NS':1})},{})
    class Client:
        def __init__(self,**kwargs):self.models=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def generate_content(self,**kwargs):
            schema=kwargs['config'].response_json_schema
            risk=schema['properties']['risk']['properties']['fact_ids']['items']['enum']
            assert 'current.max_drawdown' in risk
            assert 'current.total_return' not in risk
            assert all('.weight.' not in key for key in risk)
            return type('Response',(),{'text':json.dumps({topic:{'summary':'Historical results do not predict future outcomes.','fact_ids':['current.total_return']} for topic in ('performance','risk','comparison')})})()
    monkeypatch.setenv('GEMINI_API_KEY','mock-only')
    monkeypatch.setattr(genai,'Client',Client)
    result=interpret(r)
    assert result['status']=='ready'
    assert result['section_details']['performance']['facts'][0]['value']==facts_for(r)['current.total_return']
    assert 'benchmark.weight.NIFTYBEES.NS' not in facts_for(r)
