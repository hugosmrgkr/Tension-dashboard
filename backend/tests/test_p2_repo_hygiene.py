"""P2-08: audit repository mendeteksi berkas terlarang/secret dan repo ini bersih."""
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('audit_repo', ROOT / 'scripts/audit_repo.py')
audit_repo = importlib.util.module_from_spec(spec)
sys.modules['audit_repo'] = audit_repo
spec.loader.exec_module(audit_repo)


@pytest.mark.parametrize('path', ['.env', 'backend/.env', '.env.production', '.venv/bin/python', 'frontend/node_modules/x/index.js',
                                   'frontend/dist/index.html', 'backend/app/__pycache__/a.pyc', 'toba_local.db', 'server.pem', 'credentials.json',
                                   'data/actual/respondents.csv', 'data/private/x.csv', 'deploy/production.env', 'backups/dump.sql.gz'])
def test_forbidden_paths_are_flagged(path):
    assert audit_repo.forbidden(path)


@pytest.mark.parametrize('path', ['.env.example', 'deploy/production.env.example', 'frontend/package-lock.json', 'backend/requirements.txt',
                                   'data/sample/Data_Responden_Sintetis.csv', 'models/linear_regression_synthetic.joblib'])
def test_required_and_sample_files_are_not_flagged(path):
    assert not audit_repo.forbidden(path)


@pytest.mark.parametrize('line', ['-----BEGIN RSA PRIVATE KEY-----', 'AKIAABCDEFGHIJKLMNOP', 'ghp_' + 'a' * 36,
                                   'PASSWORD=SangatRahasia123456', 'Authorization: Bearer ' + 'x' * 40])
def test_secret_patterns_detect_real_looking_secrets(line):
    assert any(p.search(line) for p in audit_repo.SECRET_PATTERNS.values())


@pytest.mark.parametrize('line', ['POSTGRES_PASSWORD=change-me-local-only', 'POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me}', 'password=', 'VIEWER_TOKEN_SHA256=',
                                   'token: <isi>'])
def test_placeholders_are_not_secrets(line):
    assert not any(p.search(line) for p in audit_repo.SECRET_PATTERNS.values())


def test_repository_has_no_critical_findings():
    findings, _, count = audit_repo.audit()
    assert count > 100
    assert [f for f in findings if f[0] == 'KRITIS'] == []


def test_gitignore_blocks_private_and_environment_paths():
    text = (ROOT / '.gitignore').read_text(encoding='utf-8')
    for pattern in audit_repo.REQUIRED_IGNORES:
        assert pattern in text
    assert '!**/.env.example' in text
