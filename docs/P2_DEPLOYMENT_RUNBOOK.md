# Runbook Staging/Production (P2-06)

> **Status: belum diuji pada Docker.** Konfigurasi ditulis dan divalidasi sintaksnya (`docker compose config`), tetapi `up`, HTTPS, backup dan restore belum dijalankan. Uji di staging dahulu. **Jangan memuat data aktual sebelum izin dan tata kelola disetujui.** Jangan membuka URL publik sebelum security review.

## 1. Persiapan secret (sekali)
```powershell
python scripts\make_secrets.py
```
- Salin baris `POSTGRES_PASSWORD`, `VIEWER_TOKEN_SHA256`, `ADMIN_TOKEN_SHA256` ke `deploy\production.env` (salin dari `deploy\production.env.example`; file ini di-ignore Git).
- Bagikan `VIEWER_TOKEN` / `ADMIN_TOKEN` lewat kanal aman. Hanya hash yang tersimpan di server. Jangan tempel token di chat/commit/log.
- Isi `SITE_ADDRESS` (domain staging) dan `CORS_ORIGINS=https://<domain>`. Untuk latihan lokal gunakan nama host palsu (mis. `staging.test` di file hosts), **bukan** `localhost` — pagar konfigurasi menolak localhost pada staging/production.

## 2. Menjalankan
```powershell
docker compose --env-file deploy\production.env -f compose.prod.yaml up -d --build
docker compose --env-file deploy\production.env -f compose.prod.yaml ps
```
Compose berhenti dengan galat bila variabel wajib kosong. Backend menolak start bila konfigurasi tidak aman (lihat log). Database dan backend **tidak** membuka port ke host; hanya proxy (80/443).

## 3. Daftar uji staging (centang sebelum menyatakan siap)
- [ ] `https://<domain>/health` berhasil; HTTP dialihkan ke HTTPS; sertifikat valid.
- [ ] `/api/meta` tanpa token → 401; token viewer → 200; `/api/data/export/sessions` token viewer → 403, token admin → 200.
- [ ] `/api/docs` → 404; header `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options` ada.
- [ ] `docker compose ... ps` menunjukkan database tidak punya port terbuka ke host; `Test-NetConnection <host> -Port 5432` gagal dari luar.
- [ ] Log proxy tidak memuat query string (ID responden): `docker compose ... logs proxy`.
- [ ] Restart: `docker compose ... restart backend` lalu health pulih; data tetap ada.
- [ ] Backup: `BACKUP_PASSPHRASE=... ./scripts/backup_db.sh` menghasilkan berkas `.gpg` dan `.sha256`.
- [ ] Restore ke database kosong/baru berhasil; restore ke database berisi **ditolak** tanpa `RESTORE_CONFIRM=ya-timpa`.
- [ ] Jika `read_only: true` pada backend menyebabkan galat tulis, catat dan perbaiki (belum diuji).
- [ ] Security review oleh orang kedua sebelum URL dibagikan.

## 4. Operasional
- Retensi backup: `BACKUP_KEEP` (default 14 berkas terbaru). Simpan salinan di lokasi terpisah dan terenkripsi; uji restore berkala.
- Rotasi token: jalankan `make_secrets.py`, perbarui `production.env`, `docker compose ... up -d backend`, bagikan token baru.
- Jangan menjalankan `docker compose down -v`. Jangan mengubah nama project `tension-dashboard` atau volume.
- `TRUST_PROXY=true` hanya benar bila backend benar-benar di belakang proxy tepercaya (konfigurasi ini).
