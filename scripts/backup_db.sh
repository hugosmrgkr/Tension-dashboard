#!/usr/bin/env bash
# Backup PostgreSQL staging/production. Hasil dienkripsi dengan GPG simetris bila BACKUP_PASSPHRASE diisi.
# Pakai: BACKUP_PASSPHRASE=... ./scripts/backup_db.sh [folder_tujuan]   (retensi: BACKUP_KEEP=14 file terbaru)
set -euo pipefail
DEST="${1:-./backups}"; KEEP="${BACKUP_KEEP:-14}"
mkdir -p "$DEST"; chmod 700 "$DEST"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; FILE="$DEST/toba_$STAMP.sql.gz"
docker compose --env-file deploy/production.env -f compose.prod.yaml exec -T db pg_dump -U toba -d toba_health --no-owner | gzip > "$FILE"
if [ -n "${BACKUP_PASSPHRASE:-}" ]; then
  gpg --batch --yes --pinentry-mode loopback --passphrase "$BACKUP_PASSPHRASE" --symmetric --cipher-algo AES256 -o "$FILE.gpg" "$FILE" && rm -f "$FILE"; FILE="$FILE.gpg"
else
  echo "PERINGATAN: backup TIDAK terenkripsi. Isi BACKUP_PASSPHRASE untuk data aktual." >&2
fi
chmod 600 "$FILE"; sha256sum "$FILE" > "$FILE.sha256"
ls -1t "$DEST"/toba_* 2>/dev/null | grep -v '\.sha256$' | tail -n +$((KEEP+1)) | while read -r old; do rm -f "$old" "$old.sha256"; done
echo "Backup selesai: $FILE"
