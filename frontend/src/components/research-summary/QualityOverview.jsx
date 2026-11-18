
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

export default function QualityOverview({ quality }) {
  const q = quality || {};

  const daily = getCount(q.daily_records);
  const totalSessions = getCount(q.session_records);
  const validSessions = getCount(q.valid_sessions);
  const notValidSessions = getCount(q.incomplete_sessions);
  const pendingSessions = getCount(q.pending_review_sessions);

  const validPercentage = totalSessions > 0
    ? Math.min(100, validSessions / totalSessions * 100)
    : 0;

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

      <p style={{ color: '#64748b', fontSize: 13, marginTop: 0 }}>
        Hasil pemeriksaan mengikuti filter data yang sedang digunakan.
      </p>

      <div style={{ marginTop: 20 }}>
        <strong>Status sesi tekanan darah</strong>

        {totalSessions === 0 ? (
          <p style={{ color: '#64748b', fontSize: 13 }}>
            Belum ada sesi pada filter ini.
          </p>
        ) : (
          <>
            <div style={{
              display: 'flex',
              height: 14,
              overflow: 'hidden',
              borderRadius: 10,
              background: '#e5eaf1',
              marginTop: 12
            }}>
              <div
                style={{
                  width: `${validPercentage}%`,
                  background: '#27966b'
                }}
              />
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
                <strong>{whole(notValidSessions)}</strong>
              </span>
            </div>

            <p style={{ fontSize: 12, color: '#64748b' }}>
              Sesi pending review: {whole(pendingSessions)}.
              Jumlah ini ditampilkan terpisah dan tidak ditambahkan
              lagi ke total sesi.
            </p>
          </>
        )}
      </div>

      <div style={{
        borderTop: '1px solid #e5eaf1',
        marginTop: 20,
        paddingTop: 18
      }}>
        <strong>Kelengkapan catatan harian</strong>

        <p style={{ color: '#64748b', fontSize: 12 }}>
          Jumlah catatan dengan nilai kosong pada setiap variabel.
          Total catatan harian: {whole(daily)}.
        </p>

        {daily === 0 ? (
          <p style={{ color: '#64748b', fontSize: 13 }}>
            Belum ada catatan harian pada filter ini.
          </p>
        ) : (
          <div style={{
            display: 'grid',
            gap: 15,
            marginTop: 16
          }}>
            {fields.map(field => {
              const value = getCount(q[field.key]);
              const percentage = Math.min(100, value / daily * 100);

              return (
                <div key={field.key}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 12,
                    marginBottom: 6,
                    fontSize: 13
                  }}>
                    <span>{field.label}</span>
                    <strong>
                      {whole(value)} ({percentage.toFixed(1)}%)
                    </strong>
                  </div>

                  <div style={{
                    height: 9,
                    background: '#e8eef6',
                    borderRadius: 10,
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      background: '#397bc5',
                      borderRadius: 10
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div style={{
        background: '#f3f6fa',
        borderRadius: 8,
        padding: 12,
        marginTop: 18,
        fontSize: 12,
        color: '#52647a',
        lineHeight: 1.6
      }}>
        Catatan: nilai kosong tidak selalu berarti kesalahan pengisian.
        Khusus jumlah merokok, periksa juga apakah responden memang
        tidak merokok sebelum menyimpulkan bahwa datanya hilang.
      </div>
    </section>
  );
}
