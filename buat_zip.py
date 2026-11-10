
import os
import zipfile
from fnmatch import fnmatch
from pathlib import Path

# Folder utama proyek
ROOT = Path(__file__).resolve().parent

# Hasil ZIP disimpan di luar folder proyek
OUTPUT = ROOT.parent / "mental-health-dashboard-source.zip"

# Folder yang tidak perlu dimasukkan
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".idea",
    ".aws",
    ".codex",
    ".agents",
    "actual",
    "private",
    "raw",
}

# File yang tidak perlu dimasukkan
EXCLUDE_FILES = {
    ".env",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pem",
    ".key",
    ".dump",
    ".db",
    ".db-shm",
    ".db-wal",
}

count = 0

with zipfile.ZipFile(
    OUTPUT, "w", zipfile.ZIP_DEFLATED
) as zipf:

    for folder, dirs, files in os.walk(ROOT):

        # Abaikan folder tertentu
        dirs[:] = [
            d for d in dirs
            if d.lower() not in EXCLUDE_DIRS and not d.startswith('pytest-cache-files-')
        ]

        for filename in files:
            filepath = Path(folder) / filename
            relative = filepath.relative_to(ROOT)

            # Abaikan file rahasia dan cache
            if filename in EXCLUDE_FILES:
                continue

            if any(fnmatch(filename.lower(), pattern) for pattern in ('credentials*.json', 'service-account*.json')):
                continue

            if filename.startswith(".env.") and filename != ".env.example":
                continue

            if filepath.suffix.lower() in EXCLUDE_SUFFIXES or filepath.is_symlink():
                continue

            if filepath.resolve() == OUTPUT.resolve():
                continue

            zipf.write(
                filepath,
                Path(ROOT.name) / relative
            )

            count += 1

print("ZIP berhasil dibuat!")
print(f"Lokasi: {OUTPUT}")
print(f"Jumlah file: {count}")
