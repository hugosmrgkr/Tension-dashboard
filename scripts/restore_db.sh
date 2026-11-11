#!/usr/bin/env bash
# Restore ke database KOSONG/BARU. Menolak menimpa database berisi data kecuali RESTORE_CONFIRM=ya-timpa.
# Pakai: [BACKUP_PASSPHRASE=...] ./scripts/restore_db.sh file_backup(.sql.gz|.sql.gz.gpg)
set -euo pipefail
FILE="${1:?Beri path file backup}"
[ -f "$FILE.sha256" ] && sha256sum -c "$FILE.sha256"
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
case "$FILE" in
  *.gpg) gpg --batch --yes --pinentry-mode loopback --passphrase "${BACKUP_PASSPHRASE:?Isi BACKUP_PASSPHRASE}" -d "$FILE" | gunzip > "$TMP" ;;
  *.gz) gunzip -c "$FILE" > "$TMP" ;;
  *) echo "Format tidak dikenal" >&2; exit 2 ;;
esac
DC=(docker compose --env-file deploy/production.env -f compose.prod.yaml)
ROWS=$("${DC[@]}" exec -T db psql -U toba -d toba_health -tAc "select coalesce(sum(n_live_tup),0) from pg_stat_user_tables" | tr -d '[:space:]')
if [ "${ROWS:-0}" != "0" ] && [ "${RESTORE_CONFIRM:-}" != "ya-timpa" ]; then
  echo "Database berisi data ($ROWS baris). Restore dibatalkan. Set RESTORE_CONFIRM=ya-timpa hanya setelah backup baru dibuat dan disetujui." >&2; exit 3
fi
"${DC[@]}" exec -T db psql -U toba -d toba_health -v ON_ERROR_STOP=1 < "$TMP"
echo "Restore selesai. Jalankan: curl -fsS https://\$SITE_ADDRESS/health"
