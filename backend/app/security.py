"""P2-06: autentikasi token + otorisasi peran, rate limiting, header keamanan, dan pagar konfigurasi produksi.

Mode dikontrol lewat environment (dibaca per permintaan agar mudah diuji):
  APP_ENV=development|staging|production   (default development)
  AUTH_MODE=off|token                      (default off; WAJIB token pada production/staging)
  VIEWER_TOKEN_SHA256 / ADMIN_TOKEN_SHA256 hash SHA-256 (hex) dari token; token asli tidak pernah disimpan di server.
  CORS_ORIGINS=https://a.example,https://b.example  (tanpa wildcard pada production)
  RATE_LIMIT_PER_MINUTE (default 240), AUTH_FAIL_LIMIT_PER_MINUTE (default 10)

Peran: viewer = baca analitik/model; admin = viewer + ekspor CSV + detail kualitas ETL.
"""
import hashlib
import hmac
import os
import re
import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse

PUBLIC_PATHS = {'/health', '/api/health'}
ADMIN_PREFIXES = ('/api/data/export/', '/api/quality')
DEFAULT_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:8080']
SECURE_ENVS = {'production', 'staging'}
HEX64 = re.compile(r'^[0-9a-f]{64}$')
_hits = defaultdict(deque)
_fails = defaultdict(deque)


def app_env():
    return os.getenv('APP_ENV', 'development').lower()


def auth_mode():
    return os.getenv('AUTH_MODE', 'off').lower()


def cors_origins():
    raw = os.getenv('CORS_ORIGINS')
    return [o.strip() for o in raw.split(',') if o.strip()] if raw else list(DEFAULT_ORIGINS)


def sha256_hex(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def validate_runtime_config():
    """Gagal tertutup: aplikasi tidak boleh menyala di staging/production dengan konfigurasi tidak aman."""
    if app_env() not in SECURE_ENVS:
        return
    problems = []
    if auth_mode() != 'token':
        problems.append('AUTH_MODE harus "token"')
    viewer, admin = os.getenv('VIEWER_TOKEN_SHA256', ''), os.getenv('ADMIN_TOKEN_SHA256', '')
    if not HEX64.match(viewer) or not HEX64.match(admin):
        problems.append('VIEWER_TOKEN_SHA256 dan ADMIN_TOKEN_SHA256 harus hash SHA-256 heksadesimal 64 karakter')
    elif hmac.compare_digest(viewer, admin):
        problems.append('Token viewer dan admin tidak boleh sama')
    if 'change-me' in os.getenv('DATABASE_URL', '') or not os.getenv('DATABASE_URL'):
        problems.append('DATABASE_URL harus diisi dan tidak boleh memakai password default')
    origins = os.getenv('CORS_ORIGINS', '')
    if not origins or '*' in origins or 'localhost' in origins or '127.0.0.1' in origins:
        problems.append('CORS_ORIGINS harus eksplisit tanpa wildcard/localhost')
    if os.getenv('ENABLE_IMPORT', 'false').lower() == 'true':
        problems.append('ENABLE_IMPORT harus false')
    if problems:
        raise RuntimeError('Konfigurasi tidak aman untuk ' + app_env() + ': ' + '; '.join(problems))


def _client(request):
    forwarded = request.headers.get('x-forwarded-for')
    return (forwarded.split(',')[0].strip() if forwarded and os.getenv('TRUST_PROXY', 'false') == 'true'
            else (request.client.host if request.client else 'unknown'))


def _limited(store, key, limit, window=60):
    now = time.monotonic()
    bucket = store[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def role_for(request):
    header = request.headers.get('authorization', '')
    if not header.lower().startswith('bearer '):
        return None
    digest = sha256_hex(header[7:].strip())
    for role, env in (('admin', 'ADMIN_TOKEN_SHA256'), ('viewer', 'VIEWER_TOKEN_SHA256')):
        expected = os.getenv(env, '')
        if HEX64.match(expected) and hmac.compare_digest(digest, expected):
            return role
    return None


def reset_state():
    _hits.clear()
    _fails.clear()


async def security_middleware(request: Request, call_next):
    path, client = request.url.path, _client(request)
    if path.startswith('/api') or path in PUBLIC_PATHS:
        if _limited(_hits, client, int(os.getenv('RATE_LIMIT_PER_MINUTE', '240'))):
            return _finish(JSONResponse({'detail': 'Terlalu banyak permintaan. Coba lagi sebentar.'}, status_code=429, headers={'Retry-After': '60'}))
    if auth_mode() == 'token' and path not in PUBLIC_PATHS and path.startswith('/api') and request.method != 'OPTIONS':
        limit = int(os.getenv('AUTH_FAIL_LIMIT_PER_MINUTE', '10'))
        if len(_fails[client]) >= limit and _limited(_fails, client, limit):
            return _finish(JSONResponse({'detail': 'Terlalu banyak percobaan autentikasi gagal.'}, status_code=429, headers={'Retry-After': '60'}))
        role = role_for(request)
        if role is None:
            _limited(_fails, client, limit + 1000)
            return _finish(JSONResponse({'detail': 'Autentikasi diperlukan.'}, status_code=401, headers={'WWW-Authenticate': 'Bearer'}))
        if path.startswith(ADMIN_PREFIXES) and role != 'admin':
            return _finish(JSONResponse({'detail': 'Peran admin diperlukan untuk sumber ini.'}, status_code=403))
        request.state.role = role
    return _finish(await call_next(request))


def _finish(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault('Cache-Control', 'no-store')
    if app_env() in SECURE_ENVS:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response
