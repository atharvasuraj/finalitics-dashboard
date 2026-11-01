from app import create_app


def test_signed_analysis_survives_a_different_instance(monkeypatch, tmp_path):
    import dashboard
    import interpretation
    report = dict(period={'observations':252}, coverage={}, excluded_dates={}, assumptions=[],
                  portfolios={'current': {'metrics': {'total_return': .1}, 'allocations': []}})
    monkeypatch.setenv('ANALYSIS_SIGNING_KEY', 'unit-test-only-signing-key')
    monkeypatch.setattr(dashboard, 'build', lambda *args: report)
    monkeypatch.setattr(interpretation, 'interpret', lambda facts: {'status': 'ready', 'facts': facts})
    config = {'TESTING': True, 'DATA_DIR': tmp_path}
    token = create_app(config).test_client().post('/dashboard/analyse', json={}).json['analysis_id']
    other = create_app(config).test_client()
    response = other.post('/dashboard/interpret', json={'analysis_id': token})
    assert response.status_code == 200
    assert response.json['facts'] == report
    assert other.post('/dashboard/interpret', json={'analysis_id': token + 'tampered'}).status_code == 400


def test_hosted_data_is_copied_to_writable_temporary_storage(monkeypatch, tmp_path):
    import app
    import shutil
    monkeypatch.setenv('VERCEL', '1')
    source = tmp_path / 'source/data/local'
    source.mkdir(parents=True)
    (source / 'prices.csv').write_text('test fixture')
    monkeypatch.setattr(app, 'ROOT', tmp_path / 'source')
    target = app.runtime_data_dir()
    try:
        assert target != source
        assert (target / 'prices.csv').read_text() == 'test fixture'
        (target / 'writable').write_text('cache')
        assert not (source / 'writable').exists()
    finally:
        shutil.rmtree(target)
