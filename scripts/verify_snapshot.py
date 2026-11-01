#!/usr/bin/env python3
"""Verify the real local snapshot through Flask with Python network calls blocked."""

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def blocked(*args, **kwargs):
    raise RuntimeError('Network disabled for offline verification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/evidence/verified-results.json')
    args = parser.parse_args()
    os.environ.pop('GOOGLE_API_KEY', None)
    os.environ.pop('GEMINI_API_KEY', None)
    socket.socket.connect = blocked
    socket.create_connection = blocked
    socket.getaddrinfo = blocked
    from app import create_app
    client = create_app({'TESTING': True}).test_client()
    sample = client.get('/portfolio-sample')
    if sample.status_code != 200:
        raise SystemExit(f'Offline verification failed: {sample.json}')
    upload = client.post('/portfolio-analyser-upload', data={'file': (BytesIO((ROOT / 'samples/portfolio.csv').read_bytes()), 'portfolio.csv')})
    if sample.json != upload.json:
        raise SystemExit('Sample and uploaded portfolio results differ')
    response = sample.json
    response.pop('chart')
    response.pop('series')  # Raw observations remain local; the checksum identifies them.
    paths = ['app.py', 'portfolio.py', 'scripts/prepare_data.py', 'scripts/verify_snapshot.py',
             'static/portfolio.js', 'static/portfolio.css', 'templates/portfolio_analyser.html',
             'templates/legacy.html', 'samples/portfolio.csv', 'requirements.txt',
             'requirements-data.txt', 'requirements-dev.txt', 'requirements-lock.txt',
             'tests/conftest.py', 'tests/test_portfolio.py', 'tests/test_app.py']
    evidence = {
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'base_revision': 'fc55e2930c8e2a0d43762f9b5122d365faf808cd',
        'checkout_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree_note': 'Restoration may be uncommitted; source_sha256 identifies the files actually verified.',
        'python': platform.python_version(), 'network': 'Python DNS and TCP connection calls blocked before importing app',
        'llm_key': 'Both API key variables removed; foundation route has no LLM call',
        'sample_upload_match': True,
        'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
        'result': response,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
