
import React from 'react';
import { whole } from '../../lib/api';

const fields = [
  { key: 'missing_sleep_hours', label: 'Durasi tidur' },
  { key: 'missing_sitting', label: 'Durasi duduk' },
  { key: 'missing_stress', label: 'Stres' },
  { key: 'missing_activity_minutes', label: 'Durasi aktivitas' },
  { key: 'missing_smoke_count', label: 'Jumlah merokok' }
];

const getCount = value => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, number) : 0;
};

function getAxisStep(max) {
  if (max <= 0) return 1;

  const rough = max / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const normalized = rough / magnitude;

  const nice = normalized <= 1 ? 1
    : normalized <= 2 ? 2
    : normalized <= 5 ? 5 : 10;

  return nice * magnitude;
}

export default function QualityOverview({ quality }) {
  const q = quality || {};

  const daily = getCount(q.daily_records);
  const totalSessions = getCount(q.session_records);
  const validSessions = getCount(q.valid_sessions);
  const incompleteSessions = getCount(q.incomplete_sessions);
  const pendingSessions = getCount(q.pending_review_sessions);

  const validPercentage = totalSessions > 0
    ? Math.min(100, validSessions / totalSessions * 100)
    : 0;

  const chartData = fields.map(field => {
    const value = getCount(q[field.key]);

    return {
      label: field.label,
      value,
      percentage: daily > 0 ? value / daily * 100 : 0
    };
  }).sort((a, b) => b.value - a.value);

  const maxValue = Math.max(...chartData.map(item => item.value), 0);
  const step = getAxisStep(maxValue);
  const axisMax = maxValue > 0
    ? Math.ceil(maxValue / step) * step
    : 1;

  const ticks = Array.from(
    { length: Math.round(axisMax / step) + 1 },
    (_, index) => index * step
  );

  // Ukuran dan posisi elemen grafik
  const width = 900;
  const plotX = 250;
  const plotWidth = 540;
  const rowHeight = 46;
  const top = 25;
  const axisY = top + chartData.length * rowHeight;
  const height = axisY + 65;

  return (
    <section style={{
      background: '#fff',
      border: '1px solid #dbe4ef',
      borderRadius: 12,
      padding: 20,
      marginBottom: 16
    }}>
      <h3 style={{ marginTop: 0, marginBottom: 6 }}>
        Ringkasan Validitas dan Kelengkapan Data
      </h3>

      <p style={{ color: '#64748b', fontSize: 13 }}>
        Hasil pemeriksaan mengikuti filter data yang sedang digunakan.
      </p>

      {/* STATUS VALIDASI TEKANAN DARAH */}
      <div style={{ marginTop: 20 }}>
        <strong>Status validasi pengukuran tekanan darah</strong>

        {totalSessions === 0 ? (
          <p style={{ color: '#64748b', fontSize: 13 }}>
            Belum ada sesi pada filter ini.
          </p>
        ) : (
          <>
            <div style={{
              height: 14,
              background: '#e5eaf1',
              borderRadius: 10,
              overflow: 'hidden',
              marginTop: 12
            }}>
              <div style={{
                width: `${validPercentage}%`,
                height: '100%',
                background: '#27966b'
              }} />
            </div>

            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
              marginTop: 10,
              fontSize: 13
            }}>
              <span style={{ color: '#27966b' }}>
                ● Valid: <strong>{whole(validSessions)}</strong>
              </span>

              <span style={{ color: '#64748b' }}>
                ● Belum masuk hitungan valid:{' '}
                <strong>{whole(incompleteSessions)}</strong>
              </span>
            </div>

            <p style={{ fontSize: 12, color: '#64748b' }}>
              Sesi pending review: {whole(pendingSessions)}.
              Sesi yang menunggu pemeriksaan ditampilkan terpisah.
            </p>
          </>
        )}
      </div>

      {/* HORIZONTAL BAR CHART */}
      <div style={{
        borderTop: '1px solid #e5eaf1',
        marginTop: 20,
        paddingTop: 18
      }}>
        <strong>Kelengkapan Catatan Harian</strong>

        <p style={{
          color: '#64748b',
          fontSize: 12,
          marginTop: 5
        }}>
          Jumlah nilai kosong berdasarkan variabel.
          Total catatan harian: {whole(daily)}.
        </p>

        {daily === 0 ? (
          <p style={{ color: '#64748b', fontSize: 13 }}>
            Belum ada catatan harian pada filter ini.
          </p>
        ) : (
          <div style={{ width: '100%', overflowX: 'auto' }}>
            <svg
              viewBox={`0 0 ${width} ${height}`}
              width="100%"
              height="auto"
              role="img"
              aria-label="Diagram batang horizontal jumlah nilai kosong berdasarkan variabel"
              style={{
                display: 'block',
                minWidth: 560,
                fontFamily: 'Arial, sans-serif'
              }}
            >
              {/* Garis sumbu dan angka X */}
              {ticks.map(tick => {
                const x = plotX + (tick / axisMax) * plotWidth;

                return (
                  <g key={tick}>
                    <line
                      x1={x}
                      y1={top - 5}
                      x2={x}
                      y2={axisY}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />

                    <text
                      x={x}
                      y={axisY + 19}
                      textAnchor="middle"
                      fill="#64748b"
                      fontSize="12"
                    >
                      {whole(tick)}
                    </text>
                  </g>
                );
              })}

              {/* Label variabel dan batang horizontal */}
              {chartData.map((item, index) => {
                const y = top + index * rowHeight;
                const barWidth = (item.value / axisMax) * plotWidth;

                return (
                  <g key={item.label}>
                    <line
                      x1={plotX}
                      y1={y + rowHeight - 3}
                      x2={plotX + plotWidth}
                      y2={y + rowHeight - 3}
                      stroke="#eef1f5"
                      strokeWidth="1"
                    />

                    <text
                      x={plotX - 15}
                      y={y + 19}
                      textAnchor="end"
                      fill="#334155"
                      fontSize="13"
                    >
                      {item.label}
                    </text>

                    <rect
                      x={plotX}
                      y={y + 3}
                      width={barWidth}
                      height={20}
                      rx="2"
                      fill="#397bc5"
                    />

                    <text
                      x={875}
                      y={y + 19}
                      textAnchor="end"
                      fill="#1e293b"
                      fontSize="12"
                      fontWeight="600"
                    >
                      {whole(item.value)} ({item.percentage.toFixed(1)}%)
                    </text>
                  </g>
                );
              })}

              {/* Judul sumbu X */}
              <text
                x={plotX + plotWidth / 2}
                y={height - 5}
                textAnchor="middle"
                fill="#475569"
                fontSize="13"
              >
                Jumlah Nilai Kosong
              </text>
            </svg>
          </div>
        )}
      </div>

      <div style={{
        background: '#f3f6fa',
        borderRadius: 8,
        padding: 12,
        marginTop: 14,
        fontSize: 12,
        color: '#52647a',
        lineHeight: 1.6
      }}>
        Catatan: nilai kosong tidak selalu berarti kesalahan pengisian.
        Khusus jumlah merokok, periksa apakah responden memang tidak
        merokok sebelum menyimpulkan bahwa datanya hilang.
      </div>
    </section>
  );
}
