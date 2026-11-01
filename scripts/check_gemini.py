"""Small, secret-safe Gemini diagnostic. Run in the shell exporting the Free-project key."""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def safe_error(exc):
    code = getattr(exc, 'code', None)
    return {'status': 'failed', 'http_status': code if isinstance(code, int) else None,
            'kind': 'timeout' if isinstance(exc, TimeoutError) or type(exc).__name__ in ('ReadTimeout', 'ConnectTimeout') or code == 504 else 'request_error'}


def run():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        print('GEMINI_API_KEY is not exported in this Terminal. No requests sent.', flush=True)
        return 1
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print('Install requirements-ai.txt with .venv/bin/python first. No requests sent.', flush=True)
        return 1
    model = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    # No key, raw exception, request URL, generated text, or prompt is printed.
    with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000, retry_options=types.HttpRetryOptions(attempts=1))) as client:
        for stage in ('model_metadata', 'minimal_generation'):
            print(f'{stage}: starting (20-second request timeout; no automatic retries)', flush=True)
            started = time.monotonic()
            try:
                if stage == 'model_metadata':
                    client.models.get(model=model)
                    result = {'status': 'ok', 'note': 'Metadata access alone does not verify inference eligibility.'}
                else:
                    options = {'max_output_tokens': 512}
                    if model == 'gemini-3.8-flash':
                        options['thinking_config'] = types.ThinkingConfig(thinking_level='LOW')
                    response = client.models.generate_content(model=model, contents='Reply only with the word OK.', config=types.GenerateContentConfig(**options))
                    result = {'status': 'ok' if response.text else 'empty_output', 'nonempty_text': bool(response.text)}
            except Exception as exc:
                result = safe_error(exc)
            result['elapsed_seconds'] = round(time.monotonic() - started, 2)
            print(json.dumps({stage: result}), flush=True)
            if result['status'] != 'ok':
                print('Stopped; no portfolio request sent. Share these status lines, never the key.', flush=True)
                return 1
    print('Both basic checks passed. Testing saved-portfolio structured commentary once (60-second request timeout).', flush=True)
    from dashboard import build
    from interpretation import interpret
    try:
        report = build({'source': 'saved', 'current': [{'symbol': 'RELIANCE', 'weight': 40}, {'symbol': 'HDFCBANK', 'weight': 30}, {'symbol': 'INFY', 'weight': 30}]}, ROOT / 'data/local', ROOT / 'data/local/cache')
        started = time.monotonic()
        result = interpret(report)
        print(json.dumps({'portfolio_commentary': {'status': result['status'], 'reason': result.get('reason'), 'http_status': result.get('http_status'), 'elapsed_seconds': round(time.monotonic()-started, 2)}}), flush=True)
        return 0 if result['status'] == 'ready' else 1
    except Exception:
        print('Saved example could not be loaded; no portfolio commentary test completed.', flush=True)
        return 1


if __name__ == '__main__':
    try:
        result_code = run()
    except Exception:
        print('Diagnostic setup failed. No raw exception is displayed; check the SDK installation and local environment.', flush=True)
        result_code = 1
    raise SystemExit(result_code)
