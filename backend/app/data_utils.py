"""Legacy hypertension data logic copied from the Streamlit prototype.

The unrelated mental-health dummy-data helper was deliberately removed.
"""
import numpy as np
import pandas as pd


# ==================================================

STATUS_URUT = ["Normal", "Pra-hipertensi", "Hipertensi Tahap 1", "Hipertensi Tahap 2"]
KELOMPOK_USIA = ["15–24", "25–34", "35–44", "45–54", "55–64"]
_BATAS_USIA = [14, 24, 34, 44, 54, 64]


def klasifikasi_tekanan(sistolik: float, diastolik: float) -> str:
    if sistolik >= 160 or diastolik >= 100:
        return "Hipertensi Tahap 2"
    if sistolik >= 140 or diastolik >= 90:
        return "Hipertensi Tahap 1"
    if sistolik >= 130 or diastolik >= 80:
        return "Pra-hipertensi"
    return "Normal"


def tambah_kelompok_usia(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        kelompok_usia=pd.cut(df["usia"], bins=_BATAS_USIA, labels=KELOMPOK_USIA)
    )


def ringkas_per_partisipan(df: pd.DataFrame) -> pd.DataFrame:
    """Satu baris per partisipan: atribut tetap + rata-rata tekanan darah + status."""
    d = df.copy()
    if "id_partisipan" not in d.columns:
        d["id_partisipan"] = [f"P{i:03d}" for i in range(1, len(d) + 1)]
    tetap = [
        c for c in [
            "usia", "jenis_kelamin", "kecamatan", "bmi",
            "aktivitas_fisik_hari_per_minggu", "pola_makan",
            "jam_tidur", "tingkat_stres", "merokok",
        ] if c in d.columns
    ]
    agg = {c: "first" for c in tetap}
    agg.update({"sistolik": "mean", "diastolik": "mean"})
    p = d.groupby("id_partisipan", as_index=False).agg(agg)
    p["status_hipertensi"] = [
        klasifikasi_tekanan(s, k) for s, k in zip(p["sistolik"], p["diastolik"])
    ]
    return tambah_kelompok_usia(p).sort_values("id_partisipan").reset_index(drop=True)


def buat_data_hipertensi_demo() -> pd.DataFrame:
    """Data sintetis prototipe: 25 partisipan x 30 hari = 750 pengukuran.

    Komposisi status per partisipan dibuat tetap (17 Normal, 5 Pra-hipertensi,
    3 Hipertensi Tahap 1) agar sama dengan desain. Atribut gaya hidup dibangun
    dari skor risiko laten sehingga korelasinya dengan tekanan darah masuk akal.
    """
    rng = np.random.default_rng(42)
    n_p, n_hari = 25, 30
    tanggal = pd.date_range("2025-10-01", periods=n_hari, freq="D")

    risiko = rng.normal(0, 1, n_p)
    urut = np.argsort(-risiko)
    status = np.empty(n_p, dtype=object)
    status[urut[:3]] = "Hipertensi Tahap 1"
    status[urut[3:8]] = "Pra-hipertensi"
    status[urut[8:]] = "Normal"

    # rata-rata tekanan darah per partisipan (jauh dari ambang agar status stabil)
    dasar = {
        "Normal": ((113, 124), (70, 77)),
        "Pra-hipertensi": ((132, 138), (82, 87)),
        "Hipertensi Tahap 1": ((143, 150), (91, 95)),
    }
    sis_p = np.array([rng.uniform(*dasar[s][0]) for s in status])
    dia_p = np.array([rng.uniform(*dasar[s][1]) for s in status])

    usia = np.clip(np.rint(rng.integers(15, 65, n_p) + 4 * risiko), 15, 64).astype(int)
    bmi = np.clip(24.5 + 2.6 * risiko + rng.normal(0, 1.6, n_p), 18, 36).round(1)
    aktivitas = np.clip(np.rint(4 - 1.4 * risiko + rng.normal(0, 1.1, n_p)), 0, 7).astype(int)
    tidur = np.clip(6.9 - 0.6 * risiko + rng.normal(0, 0.5, n_p), 4.5, 9).round(1)
    stres = np.clip(np.rint(5 + 1.6 * risiko + rng.normal(0, 1.1, n_p)), 1, 10).astype(int)
    merokok = np.where(risiko + rng.normal(0, 0.9, n_p) > 0.55, "Ya", "Tidak")
    pola = np.where(
        risiko + rng.normal(0, 0.8, n_p) > 0.15,
        "Tinggi Garam",
        rng.choice(["Seimbang", "Tinggi Lemak", "Tidak Teratur"], n_p, p=[.6, .2, .2]),
    )
    jk = rng.choice(["Laki-laki", "Perempuan"], n_p)
    kecamatan = rng.choice(["Balige", "Laguboti", "Porsea", "Ajibata", "Tampahan"], n_p)

    # efek harian bersama (supaya garis tren bergelombang) + variasi individu
    efek_hari_s = rng.normal(0, 2.2, n_hari)
    efek_hari_d = rng.normal(0, 1.6, n_hari)

    baris = []
    for i in range(n_p):
        s = np.rint(sis_p[i] + efek_hari_s + rng.normal(0, 4, n_hari)).astype(int)
        d = np.rint(dia_p[i] + efek_hari_d + rng.normal(0, 3, n_hari)).astype(int)
        for h in range(n_hari):
            baris.append(
                {
                    "id_partisipan": f"P{i + 1:03d}",
                    "tanggal": tanggal[h],
                    "usia": usia[i],
                    "jenis_kelamin": jk[i],
                    "kecamatan": kecamatan[i],
                    "bmi": bmi[i],
                    "aktivitas_fisik_hari_per_minggu": aktivitas[i],
                    "pola_makan": pola[i],
                    "jam_tidur": tidur[i],
                    "tingkat_stres": stres[i],
                    "merokok": merokok[i],
                    "sistolik": int(np.clip(s[h], 88, 190)),
                    "diastolik": int(np.clip(d[h], 52, 120)),
                }
            )

    df = pd.DataFrame(baris)
    df["status_hipertensi"] = [
        klasifikasi_tekanan(s, d) for s, d in zip(df["sistolik"], df["diastolik"])
    ]
    return df.sort_values(["tanggal", "id_partisipan"]).reset_index(drop=True)