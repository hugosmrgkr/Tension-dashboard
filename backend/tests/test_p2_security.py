"""P2-06: autentikasi token, peran viewer/admin, rate limit, header keamanan, dan pagar konfigurasi produksi."""
import pytest
from app import security
from test_cp3_stage1 import client, loaded  # noqa: F401

VIEWER, ADMIN = 'viewer-token-contoh-123', 'admin-token-contoh-456'


@pytest.fixture
def secured(loaded, monkeypatch):
    security.reset_state()
    monkeypatch.setenv('AUTH_MODE', 'token')
    monkeypatch.setenv('VIEWER_TOKEN_SHA256', security.sha256_hex(VIEWER))
    monkeypatch.setenv('ADMIN_TOKEN_SHA256', security.sha256_hex(ADMIN))
    yield loaded
    security.reset_state()


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_dev_default_is_open_and_health_is_always_public(loaded, monkeypatch):
    assert loaded.get('/api/meta').status_code == 200
    monkeypatch.setenv('AUTH_MODE', 'token')
    assert loaded.get('/health').status_code == 200 and loaded.get('/api/health').status_code == 200


def test_token_mode_rejects_missing_or_wrong_token(secured, monkeypatch):
    monkeypatch.setenv('AUTH_FAIL_LIMIT_PER_MINUTE', '100')
    for path in ['/api/meta', '/api/analytics', '/api/model/comparison', '/api/model/predict?respondent_id=SIM001']:
        assert secured.get(path).status_code == 401, path
        assert secured.get(path, headers=auth('salah')).status_code == 401, path
        assert secured.get(path, headers={'Authorization': 'Basic abc'}).status_code == 401, path


def test_viewer_can_read_but_not_export_or_see_quality(secured):
    assert secured.get('/api/meta', headers=auth(VIEWER)).status_code == 200
    assert secured.get('/api/analytics', headers=auth(VIEWER)).status_code == 200
    assert secured.get('/api/data/export/sessions', headers=auth(VIEWER)).status_code == 403
    assert secured.get('/api/quality', headers=auth(VIEWER)).status_code == 403


def test_admin_can_export_and_read_quality(secured):
    assert secured.get('/api/data/export/sessions', headers=auth(ADMIN)).status_code == 200
    assert secured.get('/api/quality', headers=auth(ADMIN)).status_code == 200
    assert secured.get('/api/analytics', headers=auth(ADMIN)).status_code == 200


def test_failed_auth_is_rate_limited_and_valid_token_still_counts_normally(secured, monkeypatch):
    monkeypatch.setenv('AUTH_FAIL_LIMIT_PER_MINUTE', '3')
    codes = [secured.get('/api/meta', headers=auth('salah')).status_code for _ in range(6)]
    assert codes[:3] == [401, 401, 401] and 429 in codes[3:]


def test_general_rate_limit_returns_429(loaded, monkeypatch):
    security.reset_state()
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '5')
    codes = [loaded.get('/api/meta').status_code for _ in range(8)]
    security.reset_state()
    assert codes[:5] == [200] * 5 and codes[-1] == 429


def test_security_headers_and_no_store(loaded):
    r = loaded.get('/api/meta')
    assert r.headers['x-content-type-options'] == 'nosniff' and r.headers['x-frame-options'] == 'DENY'
    assert r.headers['cache-control'] == 'no-store' and r.headers['referrer-policy'] == 'no-referrer'


def test_mutating_methods_are_not_exposed(secured):
    for method in ('post', 'put', 'delete', 'patch'):
        assert getattr(secured, method)('/api/analytics', headers=auth(ADMIN)).status_code == 405


def test_cors_allows_only_configured_origins(loaded):
    ok = loaded.get('/api/meta', headers={'Origin': 'http://localhost:8080'})
    bad = loaded.get('/api/meta', headers={'Origin': 'https://jahat.example'})
    assert ok.headers.get('access-control-allow-origin') == 'http://localhost:8080'
    assert 'access-control-allow-origin' not in bad.headers


GOOD = dict(APP_ENV='production', AUTH_MODE='token', DATABASE_URL='postgresql+psycopg://toba:Kuat-Dan-Panjang-1@db:5432/toba_health',
            CORS_ORIGINS='https://dashboard.contoh.ac.id', ENABLE_IMPORT='false')


def set_env(monkeypatch, **overrides):
    values = {**GOOD, 'VIEWER_TOKEN_SHA256': security.sha256_hex(VIEWER), 'ADMIN_TOKEN_SHA256': security.sha256_hex(ADMIN), **overrides}
    for key, value in values.items():
        monkeypatch.setenv(key, value) if value is not None else monkeypatch.delenv(key, raising=False)


def test_production_guard_accepts_safe_config(monkeypatch):
    set_env(monkeypatch)
    security.validate_runtime_config()


@pytest.mark.parametrize('override', [
    dict(AUTH_MODE='off'), dict(VIEWER_TOKEN_SHA256='abc'), dict(ADMIN_TOKEN_SHA256=None),
    dict(DATABASE_URL='postgresql+psycopg://toba:change-me-local-only@db/toba_health'), dict(DATABASE_URL=None),
    dict(CORS_ORIGINS='*'), dict(CORS_ORIGINS='http://localhost:8080'), dict(CORS_ORIGINS=None), dict(ENABLE_IMPORT='true')])
def test_production_guard_refuses_unsafe_config(monkeypatch, override):
    set_env(monkeypatch, **override)
    with pytest.raises(RuntimeError):
        security.validate_runtime_config()


def test_same_viewer_and_admin_token_refused(monkeypatch):
    set_env(monkeypatch, ADMIN_TOKEN_SHA256=security.sha256_hex(VIEWER))
    with pytest.raises(RuntimeError):
        security.validate_runtime_config()


def test_development_is_not_blocked_by_guard(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('AUTH_MODE', 'off')
    security.validate_runtime_config()
