"""P2-08: audit kebersihan repository. Hanya membaca; tidak mengubah/menghapus berkas apa pun.

Pakai dari root project:  python scripts/audit_repo.py        (exit 1 bila ada temuan KRITIS)
Mode git: memeriksa `git ls-files` (berkas yang benar-benar terlacak). Tanpa git: memindai pohon berkas
dan menandai berkas terlarang yang TIDAK tercakup .gitignore proyek.
"""
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_GLOBS = ['.env', '*/.env', '.env.*', '*/.env.*', '.venv/*', 'venv/*', 'node_modules/*', '*/node_modules/*', 'dist/*', '*/dist/*',
                   '__pycache__/*', '*/__pycache__/*', '*.pyc', '*.db', '*.db-shm', '*.db-wal', '*.pem', '*.key', 'credentials*.json',
                   'service-account*.json', 'data/actual/*', 'data/private/*', 'data/raw/*', 'deploy/production.env', 'backups/*', '*.sql.gz', '*.sql.gz.gpg']
ALLOWED = {'.env.example', 'deploy/production.env.example'}
REQUIRED_FILES = ['frontend/package.json', 'frontend/package-lock.json', 'backend/requirements.txt', 'backend/requirements-dev.txt',
                  'backend/Dockerfile', 'frontend/Dockerfile', 'compose.yaml', '.gitignore', '.env.example', 'README.md']
REQUIRED_IGNORES = ['.env', 'node_modules/', 'dist/', '.venv/', '__pycache__/', '*.db', 'data/actual/', 'data/private/', 'deploy/production.env', 'backups/']
SECRET_PATTERNS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'aws key': re.compile(r'AKIA[0-9A-Z]{16}'),
    'github token': re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    'bearer literal': re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]{30,}'),
    'password assignment': re.compile(r'(?i)\b(?:password|passwd|secret|token)\s*[:=]\s*["\']?(?!change-me|\$\{|<|\s|$|""|\'\')[A-Za-z0-9/+_\-]{12,}'),
}
SECRET_SKIP = ('tests/', 'docs/', 'reports/', 'package-lock.json', 'scripts/audit_repo.py', 'scripts/make_secrets.py', '.example')
MAX_BYTES = 8 * 1024 * 1024
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', '.pytest_cache'}


def git_files():
    try:
        out = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        return out, True
    except (OSError, subprocess.CalledProcessError):
        return None, False


def walk_files():
    return [str(p.relative_to(ROOT)).replace('\\', '/') for p in ROOT.rglob('*')
            if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS)]


def forbidden(path):
    return path not in ALLOWED and any(fnmatch.fnmatch(path, pattern) for pattern in FORBIDDEN_GLOBS)


def audit():
    findings = []
    tracked, is_git = git_files()
    files = tracked if is_git else walk_files()
    for path in files:
        if forbidden(path):
            findings.append(('KRITIS', 'berkas terlarang ' + ('terlacak git' if is_git else 'ada di pohon berkas'), path))
        full = ROOT / path
        if full.is_file() and full.stat().st_size > MAX_BYTES:
            findings.append(('PERINGATAN', f'berkas besar ({full.stat().st_size // 1024 // 1024} MB)', path))
        if full.is_file() and not any(skip in path for skip in SECRET_SKIP) and full.stat().st_size < 2_000_000:
            try:
                text = full.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    findings.append(('KRITIS', 'indikasi secret (' + name + ')', path))
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            findings.append(('KRITIS', 'berkas wajib tidak ada', rel))
    ignore_lines = {line.strip() for line in (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()}
    for pattern in REQUIRED_IGNORES:
        if pattern not in ignore_lines:
            findings.append(('KRITIS', '.gitignore tidak memuat pola', pattern))
    return findings, is_git, len(files)


if __name__ == '__main__':
    result, is_git, count = audit()
    print(f"Mode: {'git ls-files' if is_git else 'pohon berkas (tanpa git)'} | {count} berkas diperiksa")
    for level, message, path in result:
        print(f'[{level}] {message}: {path}')
    critical = [r for r in result if r[0] == 'KRITIS']
    print('HASIL:', 'BERSIH' if not result else f'{len(critical)} kritis, {len(result) - len(critical)} peringatan')
    sys.exit(1 if critical else 0)
