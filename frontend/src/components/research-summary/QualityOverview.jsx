
import React from 'react';
import { whole } from '../../lib/api';

const fields = [
  { key: 'missing_sleep_hours', label: ['Durasi', 'Tidur'] },
  { key: 'missing_sitting', label: ['Durasi', 'Duduk'] },
  { key: 'missing_stress', label: ['Stres'] },
  { key: 'missing_activity_minutes', label: ['Durasi', 'Aktivitas'] },
  { key: 'missing_smoke_count', label: ['Jumlah', 'Merokok'] }
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

  const maxValue = Math.max(
    ...chartData.map(item => item.value),
    0
  );

  const step = getAxisStep(maxValue);
  const axisMax = maxValue > 0
    ? Math.ceil(maxValue / step) * step
    : 1;

  const ticks = Array.from(
    { length: Math.round(axisMax / step) + 1 },
    (_, index) => index * step
  );

  // Ukuran grafik
  const width = 900;
  const plotLeft = 85;
  const plotRight = 30;
  const plotTop = 40;
  const plotHeight = 275;
  const plotWidth = width - plotLeft - plotRight;
  const plotBottom = plotTop + plotHeight;
  const slotWidth = plotWidth / chartData.length;
  const barWidth = Math.min(76, slotWidth * 0.55);

  const height = 455;

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

      {/* VERTICAL BAR CHART */}
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
              aria-label="Diagram batang vertikal jumlah nilai kosong berdasarkan variabel"
              style={{
                display: 'block',
                minWidth: 560,
                fontFamily: 'Arial, sans-serif'
              }}
            >
              {/* Garis grid dan sumbu Y */}
              {ticks.map(tick => {
                const y = plotBottom -
                  (tick / axisMax) * plotHeight;

                return (
                  <g key={tick}>
                    <line
                      x1={plotLeft}
                      y1={y}
                      x2={width - plotRight}
                      y2={y}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />

                    <text
                      x={plotLeft - 12}
                      y={y + 4}
                      textAnchor="end"
                      fill="#64748b"
                      fontSize="12"
                    >
                      {whole(tick)}
                    </text>
                  </g>
                );
              })}

              {/* Batang dan label variabel */}
              {chartData.map((item, index) => {
                const centerX =
                  plotLeft + (index + 0.5) * slotWidth;

                const barHeight =
                  (item.value / axisMax) * plotHeight;

                const barY = plotBottom - barHeight;

                return (
                  <g key={item.label.join('-')}>
                    {/* Batang */}
                    <rect
                      x={centerX - barWidth / 2}
                      y={barY}
                      width={barWidth}
                      height={barHeight}
                      fill="#397bc5"
                      rx="2"
                    />

                    {/* Angka dan persentase */}
                    <text
                      x={centerX}
                      y={Math.max(plotTop - 8, barY - 10)}
                      textAnchor="middle"
                      fill="#1e293b"
                      fontSize="12"
                      fontWeight="600"
                    >
                      {whole(item.value)}
                    </text>

                    {/* Label sumbu X */}
                    <text
                      x={centerX}
                      y={plotBottom + 23}
                      textAnchor="middle"
                      fill="#334155"
                      fontSize="12"
                    >
                      {item.label.map((line, lineIndex) => (
                        <tspan
                          key={lineIndex}
                          x={centerX}
                          dy={lineIndex === 0 ? 0 : 16}
                        >
                          {line}
                        </tspan>
                      ))}
                    </text>

                    {/* Persentase di bawah label */}
                    <text
                      x={centerX}
                      y={plotBottom + 62}
                      textAnchor="middle"
                      fill="#64748b"
                      fontSize="11"
                    >
                      {item.percentage.toFixed(1)}%
                    </text>
                  </g>
                );
              })}

              {/* Judul sumbu Y */}
              <text
                transform={`translate(19 ${plotTop + plotHeight / 2}) rotate(-90)`}
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
