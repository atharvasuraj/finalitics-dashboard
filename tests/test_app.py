from io import BytesIO

import pytest

from app import ROOT, create_app


@pytest.fixture
def client(snapshot):
    return create_app({"TESTING": True, "DATA_DIR": snapshot}).test_client()


def test_sample_equals_uploaded_csv_offline(client):
    sample = client.get('/portfolio-sample')
    upload = client.post('/portfolio-analyser-upload', data={'file': (BytesIO((ROOT / 'samples/portfolio.csv').read_bytes()), 'portfolio.csv')})
    assert sample.status_code == upload.status_code == 200
    assert sample.json == upload.json
    assert sample.json['chart'].startswith('iVBOR')
    assert not {'forecast', 'llm_analysis', 'tech_data'} & sample.json.keys()
    home = client.get('/')
    assert home.status_code == 200
    assert b'Finalitics' in home.data
    assert client.get('/portfolio-analyser').status_code == 200
    assert client.get('/sample-portfolio.csv').data == (ROOT / 'samples/portfolio.csv').read_bytes()
    assert client.get('/health').json['mode'] == 'offline'


def test_errors_and_recovery(client):
    assert client.post('/portfolio-analyser-upload').status_code == 400
    invalid = client.post('/portfolio-analyser-upload', data={'file': (BytesIO(b'Symbol,Weight\nINFY,80\n'), 'bad.csv')})
    assert invalid.status_code == 400
    assert '80%' in invalid.json['error']
    assert client.post('/portfolio-analyser-upload', data={'file': (BytesIO(b'x' * (1024 * 1024 + 1)), 'large.csv')}).status_code == 413
    assert client.post('/portfolio-analyser-upload', data={'file': (BytesIO(b'{}'), 'wrong.json')}).status_code == 400
    assert client.get('/portfolio-sample').status_code == 200


def test_data_failure_is_explicit(client, snapshot):
    (snapshot / 'prices.csv').unlink()
    response = client.get('/portfolio-sample')
    assert response.status_code == 503
    assert 'prepare_data.py' in response.json['error']
    assert client.get('/health').status_code == 503


@pytest.mark.parametrize('path', ['/upload', '/sample-data', '/stock-offerings', '/personal-mf', '/personal-mf-table'])
def test_legacy_analysis_cannot_return_fabricated_metrics(client, path):
    for method in (client.get, client.post):
        response = method(path)
        assert response.status_code == 410
        assert 'disabled' in response.json['error']


def test_guided_dashboard_template_has_all_controller_targets(client):
    import re
    from bs4 import BeautifulSoup
    html=BeautifulSoup(client.get('/dashboard').data,'html.parser')
    ids=[tag['id'] for tag in html.select('[id]')]
    assert len(ids)==len(set(ids))
    source=(ROOT/'static/dashboard.js').read_text()
    referenced=set(re.findall(r'\$\("([A-Za-z][A-Za-z0-9]*)"\)',source))
    assert referenced.issubset(set(ids)), referenced-set(ids)
    assert len(html.select('[role=tab]'))==4
    assert html.select_one('#buildStage') is not None
    assert html.select_one('#exploreStage').has_attr('hidden')
    script = html.select_one('script[type=module][src*="/static/dashboard.js"]')['src']
    assert script.startswith('/static/dashboard.js?v=')
    assert script.split('?v=')[1].isdigit()


def test_local_interface_reload_and_cache_policy(client):
    assert client.application.config['TEMPLATES_AUTO_RELOAD'] is True
    assert client.application.jinja_env.auto_reload is True
    for path in ('/', '/dashboard', '/static/dashboard.js', '/static/dashboard.css'):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers['Cache-Control'] == 'no-store'
    with client.application.test_request_context():
        # The same helper is available in every template, including the home.
        context = {}
        client.application.update_template_context(context)
        assert context['asset_url']('dashboard.js') == (
            f'/static/dashboard.js?v={(ROOT / "static/dashboard.js").stat().st_mtime_ns}'
        )


def test_home_preview_uses_fixed_saved_payload(snapshot, monkeypatch):
    import dashboard
    calls = []
    def saved_build(payload, data_dir, cache):
        calls.append((payload, data_dir, cache))
        return {'dates': ['2022-01-03', '2024-12-31'], 'portfolios': {}}
    monkeypatch.setattr(dashboard, 'build', saved_build)
    client = create_app({'TESTING': True, 'DATA_DIR': snapshot}).test_client()
    # Query input cannot turn the landing preview into a provider request.
    response = client.get('/home-preview?source=historical&symbol=TCS.NS')
    assert response.status_code == 200
    assert response.json['dates'] == ['2022-01-03', '2024-12-31']
    assert len(calls) == 1
    payload, data_dir, cache = calls[0]
    assert payload == {
        'source': 'saved', 'start': '2022-01-01', 'end': '2024-12-31',
        'current': [
            {'symbol': 'RELIANCE.NS', 'weight': 40},
            {'symbol': 'HDFCBANK.NS', 'weight': 30},
            {'symbol': 'INFY.NS', 'weight': 30},
        ],
        'alternative': [
            {'symbol': 'RELIANCE.NS', 'weight': 20},
            {'symbol': 'HDFCBANK.NS', 'weight': 40},
            {'symbol': 'INFY.NS', 'weight': 40},
        ],
    }
    assert data_dir == snapshot
    assert cache == snapshot / 'cache'


def test_home_preview_missing_snapshot_fails_explicitly(client, snapshot):
    (snapshot / 'prices.csv').unlink()
    response = client.get('/home-preview')
    assert response.status_code == 503
    assert 'prepare_data.py' in response.json['error']


def test_home_preview_missing_benchmark_does_not_retrieve(client, monkeypatch):
    import yfinance
    def provider_forbidden(*args, **kwargs):
        raise AssertionError('The home preview must not call a provider.')
    monkeypatch.setattr(yfinance, 'Ticker', provider_forbidden)
    response = client.get('/home-preview')
    assert response.status_code == 503
    assert 'saved benchmark cache is missing' in response.json['error']
