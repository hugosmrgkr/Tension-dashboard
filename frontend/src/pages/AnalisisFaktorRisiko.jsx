
import React from 'react';
import {
  Activity,
  CalendarDays,
  HeartPulse,
  UsersRound,
  ClipboardCheck,
} from 'lucide-react';

import { Card, Notice, MiniTable, Empty } from '../components/Common';

import {
  SessionBox,
  NumericScatter,
  StressBox,
  CategoryBars,
  PieCategories,
  WorkTreemap,
  SmallMultiples,
} from '../components/Visuals';

import { fmt, whole } from '../lib/api';
import { ChartCard, Explainer } from '../components/page-shared/Analysis';

// Ringkasan jumlah catatan dan responden unik
const dailySample = (rows = []) =>
  `${whole(rows.length)} pasangan ID-tanggal dari ${whole(
    new Set(rows.map((row) => row.respondent_id)).size,
  )} ID unik`;

// Ringkasan jumlah catatan pada kategori
const categorySample = (rows = []) =>
  `${whole(rows.reduce((sum, row) => sum + (row.n || 0), 0))} catatan harian valid; jumlah ID unik tersedia pada tooltip`;

// Komponen kartu indikator utama
function RiskKpi({ icon: Icon, label, value, description }) {
  return (
    <div className="kpi kpi-biru">
      <div className="kpi-ico">
        <Icon size={22} />
      </div>

      <div className="kpi-content">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        <div className="kpi-sub">{description}</div>
      </div>
    </div>
  );
}

// Ringkasan kualitas data berdasarkan filter aktif
function RiskDataQuality({ quality }) {
  if (!quality) {
    return (
      <Card title="Kualitas data pada filter aktif">
        <Notice>Kualitas data belum tersedia dari API.</Notice>
      </Card>
    );
  }

  const completeness = quality.daily_records
    ? (100 *
        (quality.daily_records -
          (quality.missing_sleep_hours || 0))) /
      quality.daily_records
    : null;

  const items = [
    ['Catatan harian', whole(quality.daily_records)],
    ['Sesi tercatat', whole(quality.session_records)],
    ['Sesi valid', whole(quality.valid_sessions)],
    ['Sesi tidak lengkap', whole(quality.incomplete_sessions)],
    ['Tidur kosong', whole(quality.missing_sleep_hours)],
    ['Stres kosong', whole(quality.missing_stress)],
    ['Aktivitas kosong', whole(quality.missing_activity_minutes)],
    ['Jumlah merokok kosong', whole(quality.missing_smoke_count)],
  ];

  return (
    <Card title="Kualitas data pada filter aktif" icon={ClipboardCheck}>
      <div className="quality-grid">
        {items.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <b>{value}</b>
          </div>
        ))}
      </div>

      <Explainer>
        Missing dihitung dari catatan harian pada filter yang sedang aktif.
        Data kosong tidak diubah menjadi nol.
        Persentase kelengkapan tidur{' '}
        {completeness == null
          ? 'belum dapat dihitung'
          : `${fmt(completeness, 1)}%`}.
        Ukuran ini hanya menggambarkan ketersediaan kolom tidur,
        bukan kualitas seluruh data.
      </Explainer>
    </Card>
  );
}

// Halaman utama Analisis Faktor Risiko
export default function FaktorRisiko({ data, onFilter }) {
  if (!data || data.empty || data.kpis?.sessions === 0) {
    return <Empty message={data?.message} />;
  }

  const k = data.kpis || {};
  const q = data.filtered_quality || {};
  const d = data.scatter || [];
  const c = data.categories || {};

  // Mengambil pasangan data numerik yang valid
  const numeric = (field) =>
    d.filter(
      (row) =>
        Number.isFinite(row[field]) &&
        Number.isFinite(row.sbp_mean),
    );

  // Komponen grafik kategori
  const category = (field, title, description) => (
    <ChartCard
      key={field}
      title={title}
      sample={categorySample(c[field] || [])}
      description={description}
    >
      <CategoryBars rows={c[field] || []} />
    </ChartCard>
  );

  return (
    <>
      {/* Penanda dataset sintetis */}
      {data.source_kind === 'synthetic' && (
        <Notice tone="warning">
          Dataset yang sedang ditampilkan masih berupa data
          sintetis/simulasi. Visualisasi ini digunakan untuk menguji
          tampilan dan alur analisis, bukan sebagai temuan penelitian
          responden aktual.
        </Notice>
      )}

      <Notice>
        Analisis ini bersifat deskriptif. Hubungan faktor gaya hidup
        dengan tekanan darah tidak membuktikan sebab-akibat dan bukan
        diagnosis medis. Semua ringkasan mengikuti filter global.
      </Notice>

      {/* Kartu indikator utama */}
      <div className="kpi-grid">
        <RiskKpi
          icon={UsersRound}
          label="Responden pada filter"
          value={whole(k.respondents)}
          description="ID unik dengan catatan harian"
        />

        <RiskKpi
          icon={CalendarDays}
          label="Catatan harian"
          value={whole(k.daily_records)}
          description="Satu catatan untuk setiap ID-tanggal"
        />

        <RiskKpi
          icon={Activity}
          label="Sesi tekanan darah valid"
          value={whole(k.sessions)}
          description="Sesi yang lolos pemeriksaan teknis"
        />

        <RiskKpi
          icon={HeartPulse}
          label="Rerata SBP sesi"
          value={`${fmt(k.mean_sbp, 1)} mmHg`}
          description="Rerata seluruh sesi valid pada filter"
        />
      </div>

      {/* Ringkasan kualitas data */}
      <RiskDataQuality quality={q} />

      <p className="interaction-hint">
        Klik titik pada grafik scatter untuk memperinci responden
        dan tanggal melalui filter global. Ringkasan, grafik, dan
        data ekspor akan mengikuti filter yang dipilih.
      </p>

      {/* Visualisasi faktor risiko */}
      <div className="page-grid two">

        <ChartCard
          title="Durasi tidur dan SBP harian"
          sample={dailySample(numeric('sleep_hours'))}
          description="Durasi tidur dinyatakan dalam jam. Setiap titik mewakili pasangan ID-tanggal. Pola titik menunjukkan asosiasi, bukan pengaruh kausal."
        >
          <NumericScatter
            rows={d}
            xkey="sleep_hours"
            xlabel="Tidur (jam)"
            onSelect={onFilter}
          />
        </ChartCard>

        <ChartCard
          title="SBP harian menurut tingkat stres"
          sample={dailySample(numeric('stress'))}
          description="Skala stres mengikuti isian formulir. Bandingkan sebaran dan ukuran tiap kelompok; jumlah catatan antar-kelompok dapat berbeda."
        >
          <StressBox rows={d} />
        </ChartCard>

        <ChartCard
          title="Aktivitas fisik dan SBP harian"
          sample={dailySample(numeric('activity_minutes'))}
          description="Aktivitas dinyatakan dalam menit per hari. Nilai nol yang benar-benar diisi tetap valid, sedangkan missing tidak diubah menjadi nol."
        >
          <NumericScatter
            rows={d}
            xkey="activity_minutes"
            xlabel="Aktivitas (menit/hari)"
            onSelect={onFilter}
          />
        </ChartCard>

        <ChartCard
          title="Distribusi DBP menurut kelompok usia"
          sample={`${whole((data.session_box || []).length)} sesi valid`}
          description="Distribusi DBP sesi dikelompokkan berdasarkan usia. Ukuran kelompok dapat berbeda sehingga hasil perlu dibaca bersama jumlah datanya."
        >
          <SessionBox
            rows={data.session_box || []}
            group="age_group"
            field="dbp_mean"
            violin
          />
        </ChartCard>

        {category(
          'salty_food',
          'Makanan asin dan SBP harian',
          'Kategori frekuensi mengikuti formulir. Perbedaan rerata antar-kategori dapat dipengaruhi faktor lain dan bukan bukti pengaruh makanan asin.',
        )}

        <ChartCard
          title="Komposisi konsumsi buah"
          sample={categorySample(c.fruit || [])}
          description="Proporsi catatan ID-tanggal yang memiliki jawaban buah dan SBP valid, bukan persentase responden unik. Missing tidak masuk penyebut."
        >
          <PieCategories rows={c.fruit || []} />
        </ChartCard>

        <ChartCard
          title="Komposisi konsumsi sayur"
          sample={categorySample(c.vegetable || [])}
          description="Proporsi catatan harian terukur menurut kategori konsumsi sayur. Grafik ini tidak mengukur efek diet secara terkontrol."
        >
          <PieCategories rows={c.vegetable || []} />
        </ChartCard>

        <ChartCard
          title="Jenis aktivitas pada catatan harian"
          sample={categorySample(c.activity_type || [])}
          description="Luas bidang menunjukkan jumlah catatan ID-tanggal pada kategori aktivitas dengan SBP valid."
        >
          <WorkTreemap rows={c.activity_type || []} />
        </ChartCard>

        {category(
          'caffeine',
          'Kafein dan SBP harian',
          'Kategori konsumsi kafein mengikuti jawaban formulir. Jumlah catatan dan ID unik perlu diperhatikan saat membandingkan kategori.',
        )}

        {category(
          'smoked',
          'Status merokok dan SBP harian',
          'Status tidak merokok merupakan kategori tersendiri. Data jumlah rokok yang kosong tidak boleh dianggap nol.',
        )}

        <ChartCard
          title="Jumlah merokok dan SBP harian"
          sample={dailySample(numeric('smoke_count'))}
          description="Jumlah mengikuti isian harian. Hanya pasangan data lengkap yang ditampilkan; missing yang tinggi membatasi interpretasi."
        >
          <NumericScatter
            rows={d}
            xkey="smoke_count"
            xlabel="Jumlah merokok (kali/hari)"
            onSelect={onFilter}
          />
        </ChartCard>

        {category(
          'medication',
          'Kepatuhan obat dan SBP harian',
          'Tidak menggunakan obat berbeda makna dengan tidak patuh mengonsumsi obat. Kategori ini tidak membuktikan efek obat.',
        )}

        {category(
          'sitting',
          'Waktu duduk dan SBP harian',
          'Durasi duduk disajikan sebagai kategori sesuai formulir, bukan angka jam kontinu. Perhatikan ukuran setiap kelompok.',
        )}

        <ChartCard
          title="Tren SBP menurut kelompok usia"
          sample={`${whole(k.sessions)} sesi valid`}
          description="Setiap panel memperlihatkan pola SBP menurut kelompok usia dengan rentang sumbu yang sama. Komposisi responden dapat berubah antar-tanggal."
        >
          <SmallMultiples rows={data.small_multiples || []} />
        </ChartCard>
      </div>

      {/* Tabel korelasi */}
      <Card title="Ringkasan asosiasi numerik dengan SBP harian">
        <MiniTable
          rows={(data.correlations || []).map((row) => ({
            ...row,
            field: ({
              sleep_hours: 'Durasi tidur (jam)',
              stress: 'Tingkat stres',
              activity_minutes: 'Aktivitas (menit)',
              smoke_count: 'Jumlah merokok',
            })[row.field] || row.field,
            r: fmt(row.r, 3),
          }))}
          columns={[
            ['field', 'Variabel'],
            ['n', 'Pasangan ID-tanggal'],
            ['respondents', 'ID unik'],
            ['r', 'Korelasi Pearson (r)'],
          ]}
        />

        <Explainer>
          Nilai Pearson r berada pada rentang -1 sampai 1 dan
          merangkum hubungan linear pada data yang tersedia.
          Nilai tidak dihitung jika pasangan data kurang dari tiga
          atau salah satu variabel tidak memiliki variasi.
          Korelasi bukan uji sebab-akibat dan tidak otomatis
          menunjukkan hubungan yang signifikan secara statistik.
        </Explainer>
      </Card>
    </>
  );
}
