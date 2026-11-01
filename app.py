"""Finalitics: restored offline historical stock-portfolio demonstration.

The collaborative 2025 implementation is preserved in Git history and the
original notebooks. Legacy analysis endpoints are intentionally disabled.
"""

import base64
from io import BytesIO
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
if os.environ.get("VERCEL"):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/finalitics-matplotlib")

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from werkzeug.exceptions import RequestEntityTooLarge

from portfolio import ASSUMPTIONS, DataError, InputError, analyse, load_snapshot

ROOT = Path(__file__).resolve().parent


def runtime_data_dir():
    if not os.environ.get('VERCEL'):
        return ROOT / 'data/local'
    # Vercel's source bundle is read-only. Each instance gets a private,
    # ephemeral copy; raw prices are never exposed as static assets.
    import shutil
    import tempfile
    target = Path(tempfile.mkdtemp(prefix='finalitics-'))
    source = ROOT / 'data/local'
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True)
    return target


def chart_png(series):
    from datetime import date
    figure = Figure(figsize=(9, 3.6), layout='constrained')
    axes = figure.subplots()
    axes.plot([date.fromisoformat(point['date']) for point in series],
              [point['index'] for point in series], color='#3498db', linewidth=1.5)
    axes.axhline(100, color='#888888', linestyle='--', linewidth=0.7)
    axes.set(title='Historical portfolio index · buy and hold', xlabel='Trading date', ylabel='Index (start = 100)')
    axes.grid(alpha=0.2)
    figure.autofmt_xdate()
    with BytesIO() as buffer:
        figure.savefig(buffer, format='png', dpi=140)
        return base64.b64encode(buffer.getvalue()).decode('ascii')


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_mapping(
        MAX_CONTENT_LENGTH=1024 * 1024,
        DATA_DIR=runtime_data_dir(),
        TEMPLATES_AUTO_RELOAD=True,
    )
    if test_config:
        application.config.update(test_config)
    application.jinja_env.auto_reload = True

    @application.context_processor
    def versioned_assets():
        def asset_url(filename):
            asset = Path(application.static_folder) / filename
            return url_for('static', filename=filename, v=asset.stat().st_mtime_ns)
        return {'asset_url': asset_url}

    @application.after_request
    def avoid_stale_interface(response):
        # A long-running local server must not combine a cached HTML template
        # or controller with newer controls after a source update.
        if response.mimetype in (
            'text/html', 'text/css', 'text/javascript', 'application/javascript',
        ):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @application.get('/')
    def index():
        return render_template('home.html')

    from collections import OrderedDict
    from threading import Lock
    import time, uuid
    from dashboard import build, csv_allocation
    from interpretation import interpret
    reports = OrderedDict()
    lock = Lock()

    @application.get('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @application.get('/home-preview')
    def home_preview():
        # This route is deliberately fixed to the local saved example.
        # build(source='saved') reads the snapshot and cached ETF only; it
        # never retrieves prices, even if query parameters request it.
        report = build({
            'source': 'saved',
            'start': '2022-01-01',
            'end': '2024-12-31',
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
        }, Path(application.config['DATA_DIR']),
            Path(application.config['DATA_DIR']) / 'cache')
        return jsonify(report)

    @application.post('/dashboard/csv')
    def dashboard_csv():
        if 'file' not in request.files:
            raise InputError('Select an allocation CSV.')
        return jsonify(rows=csv_allocation(request.files['file'].read()))

    @application.post('/dashboard/analyse')
    def dashboard_analyse():
        report = build(request.get_json(silent=True), Path(application.config['DATA_DIR']),
                       Path(application.config['DATA_DIR']) / 'cache')
        identifier = uuid.uuid4().hex
        signing_key = os.environ.get('ANALYSIS_SIGNING_KEY')
        if signing_key:
            # Only interpretation facts are signed, never the large price series.
            from itsdangerous import URLSafeTimedSerializer
            facts = {k: report[k] for k in ('period', 'coverage', 'excluded_dates', 'assumptions')}
            facts['portfolios'] = {n: {k: p[k] for k in ('metrics', 'allocations')}
                                   for n, p in report['portfolios'].items()}
            identifier = URLSafeTimedSerializer(signing_key, salt='analysis-v1').dumps(facts)
        with lock:
            reports[identifier] = (time.monotonic(), report)
            while len(reports) > 32:
                reports.popitem(last=False)
        return jsonify({**report, "analysis_id": identifier})

    @application.post('/dashboard/interpret')
    def dashboard_interpret():
        body = request.get_json(silent=True)
        identifier = body.get('analysis_id') if isinstance(body, dict) else None
        entry = None
        signing_key = os.environ.get('ANALYSIS_SIGNING_KEY')
        if signing_key and isinstance(identifier, str):
            from itsdangerous import URLSafeTimedSerializer, BadData
            try:
                facts = URLSafeTimedSerializer(signing_key, salt='analysis-v1').loads(identifier, max_age=3600)
                return jsonify(interpret(facts))
            except BadData:
                raise InputError('Analysis expired or invalid. Calculate again before requesting commentary.')
        with lock:
            entry = reports.get(identifier) if isinstance(identifier, str) else None
        if entry is None or time.monotonic()-entry[0] > 3600:
            raise InputError('Analysis expired or server restarted. Calculate again before requesting commentary.')
        return jsonify(interpret(entry[1]))

    @application.get('/portfolio-analyser')
    def portfolio_page():
        return render_template('portfolio_analyser.html', assumptions=ASSUMPTIONS)

    def result(raw):
        payload = analyse(raw, Path(application.config['DATA_DIR']))
        payload['chart'] = chart_png(payload['series'])
        return jsonify(payload)

    @application.errorhandler(InputError)
    def invalid_input(exc):
        return jsonify(error=str(exc)), 400

    @application.errorhandler(DataError)
    def unavailable_data(exc):
        return jsonify(error=str(exc)), 503

    @application.errorhandler(RequestEntityTooLarge)
    def oversized_file(exc):
        return jsonify(error='Upload exceeds the 1 MB limit. Use a small portfolio CSV.'), 413

    @application.errorhandler(500)
    def unexpected_error(exc):
        return jsonify(error='Analysis failed unexpectedly. Check the local server log and try again.'), 500

    @application.post('/portfolio-analyser-upload')
    def portfolio_upload():
        if 'file' not in request.files or not request.files['file'].filename:
            raise InputError('Select a portfolio CSV first.')
        uploaded = request.files['file']
        if not uploaded.filename.lower().endswith('.csv'):
            raise InputError('Upload a .csv file with Symbol,Weight columns.')
        return result(uploaded.read())

    @application.get('/portfolio-sample')
    def portfolio_sample():
        return result((ROOT / 'samples/portfolio.csv').read_bytes())

    @application.get('/sample-portfolio.csv')
    def sample_csv():
        return send_from_directory(ROOT / 'samples', 'portfolio.csv', as_attachment=True)

    @application.get('/health')
    def health():
        try:
            _, metadata = load_snapshot(Path(application.config['DATA_DIR']))
        except DataError as exc:
            return jsonify(status='data_unavailable', error=str(exc), mode='offline'), 503
        return jsonify(status='ready', mode='offline', dataset_sha256=metadata['sha256'])

    @application.get('/legacy')
    @application.get('/stock-offerings-page')
    def legacy_page():
        return render_template('legacy.html')

    def legacy_disabled():
        return jsonify(error='Legacy/unverified analysis is disabled. Use /portfolio-analyser for saved-data historical stock analysis.'), 410

    for path in ('/upload', '/sample-data', '/stock-offerings', '/personal-mf', '/personal-mf-table'):
        application.add_url_rule(path, endpoint='legacy_' + path.strip('/'), view_func=legacy_disabled, methods=['GET', 'POST'])
    return application


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5001'))
    print(f'Finalitics: http://127.0.0.1:{port}/')
    app.run(host='127.0.0.1', port=port, debug=False)
