# Branding dan Penamaan Proyek (P2-07)

Status: **nama tampilan sudah konsisten; nama folder/repository menunggu konfirmasi tim/dosen.**

## Nama resmi yang dipakai di antarmuka
**Toba Health Insight** (judul tab browser, sidebar, footer, judul API, judul README, docstring backend). Pengujian otomatis `backend/tests/test_p2_branding.py` menjaga konsistensi ini dan gagal bila ada teks antarmuka yang kembali memuat nama lama (`mental-health`).

## Nama yang SENGAJA tidak diubah (mengubahnya merusak data/skrip yang berjalan)
| Nama | Alasan |
|---|---|
| Project Docker `tension-dashboard` (`docker compose -p`) | Menentukan nama volume PostgreSQL utama. Mengubahnya membuat volume baru yang kosong dan data lama tampak hilang. |
| Database `toba_health`, user `toba` | Terpakai oleh `compose.yaml`, `compose.prod.yaml`, skrip backup/restore, dan `DATABASE_URL` yang ada. |
| Volume `postgres_data` / `toba_prod_pgdata` | Berisi data. Jangan dihapus atau diganti. |

## Referensi nama lama yang masih ada (menunggu keputusan nama repository)
| Lokasi | Isi | Tindakan setelah nama final disetujui |
|---|---|---|
| `buat_zip.py` baris `OUTPUT = ...mental-health-dashboard-source.zip` | Nama berkas ZIP keluaran | Ganti nama keluaran dan ubah rujukan yang sama di `backend/tests/test_source_archive.py` |
| `backend/tests/test_source_archive.py` | Membuka ZIP dengan nama lama | Ikuti perubahan `buat_zip.py` |
| `backend/app/data_utils.py` (docstring) | Catatan sejarah bahwa helper lama dihapus | Tidak perlu diubah |
| Folder arsip `Tension-dashboard` / `mental-health-dashboard` | Nama folder/repository | Rename terencana, lihat prosedur |

## Prosedur rename yang aman (jalankan hanya setelah nama disetujui)
1. Konfirmasi tertulis nama repository/folder dari tim/dosen; catat di commit.
2. Buat branch `chore/rename-project`; jangan menyentuh `-p tension-dashboard` dan nama database/volume.
3. Rename folder/repository, lalu `grep -rIn "<nama lama>" --exclude-dir=node_modules --exclude-dir=reports .` dan perbarui hasilnya (kecuali tabel "sengaja tidak diubah").
4. Jalankan `pytest backend/tests`, `npm test`, `npm run build`, dan `docker compose -p tension-dashboard config -q`.
5. Pastikan `docker volume ls` masih memuat volume lama dan `http://localhost:8080/api/meta` menampilkan jumlah data yang sama.
