
import React, { useEffect, useState } from "react";

import {
  AlertTriangle,
  Activity,
  HeartPulse,
  Target,
  UsersRound,
  ChartColumn,
  TableProperties,
  ArrowRight,
} from "lucide-react";

import {
  Card,
  Status,
  Empty,
  Notice,
} from "../components/Common";

import { FilterPanel } from "../components/Filters";

import {
  AgeBars,
  CorrHeatmap,
  Confusion,
  DistributionLegend,
  Donut,
  ModelBars,
  ModelDonut,
  TrendPlot,
} from "../components/Charts";

import {
  api,
  queryString,
  fmt,
  whole,
} from "../lib/api";

// Komponen KPI
function KPI({ tone, Icon, label, value, sub }) {
  return (
    <div className={`kpi kpi-${tone}`}>
      <div className="kpi-ico">
        <Icon size={23} />
      </div>

      <div className="kpi-content">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        <div className="kpi-sub">{sub}</div>
      </div>
    </div>
  );
}

export default function Dashboard({
  summary,
  meta,
  filters,
  setFilters,
  model,
  changePage,
}) {
  const [participant, setParticipant] = useState(
    "Semua Partisipan"
  );

  const [single, setSingle] = useState([]);
  const filterKey = JSON.stringify(filters);

  // Mengambil tren untuk satu partisipan
  useEffect(() => {
    if (participant === "Semua Partisipan") {
      setSingle([]);
      return;
    }

    let active = true;

    api(
      "/measurements" +
        queryString(JSON.parse(filterKey), {
          id_partisipan: participant,
          page_size: 1000,
        })
    )
      .then((response) => {
        if (active) {
          setSingle(
            response.rows.map((row) => ({
              tanggal: row.tanggal,
              sistolik_mean: row.sistolik,
              diastolik_mean: row.diastolik,
            }))
          );
        }
      })
      .catch((err) => {
        console.error(
          "Gagal memuat data partisipan:",
          err
        );

        if (active) {
          setSingle([]);
        }
      });

    return () => {
      active = false;
    };
  }, [participant, filterKey]);

  // Reset pilihan partisipan ketika filter berubah
  useEffect(() => {
    setParticipant("Semua Partisipan");
  }, [filterKey]);

  return (
    <div className="dashboard-layout">
      <div className="dashboard-content">
        {summary?.empty ? (
          <Empty />
        ) : (
          <>
            {/* Kartu KPI */}
            <div className="kpi-grid">
              <KPI
                tone="biru"
                Icon={UsersRound}
                label="Jumlah Partisipan"
                value={whole(summary.total_participants)}
                sub="Usia produktif (15–64 tahun)"
              />

              <KPI
                tone="hijau"
                Icon={HeartPulse}
                label="Total Pengukuran"
                value={whole(summary.total_rows)}
                sub={`Data selama ${summary.days} hari`}
              />

              <KPI
                tone="merah"
                Icon={AlertTriangle}
                label="Di Atas Rentang Normal"
                value={
                  <>
                    {summary.non_normal}
                    <small className="kpi-pct">
                      ({fmt(
                        summary.non_normal_percent,
                        0
                      )}%)
                    </small>
                  </>
                }
                sub="Pra-hipertensi + Hipertensi"
              />

              <KPI
                tone="ungu"
                Icon={Activity}
                label="Rata-rata Tekanan Darah"
                value={
                  <>
                    {fmt(summary.mean_sistolik, 0)}/
                    {fmt(summary.mean_diastolik, 0)}
                    <small>mmHg</small>
                  </>
                }
                sub="Sistolik / Diastolik"
              />
            </div>

            {/* Grafik utama */}
            <div className="dashboard-row dashboard-row-one">
              <Card title="Tren Tekanan Darah Rata-rata">
                <div className="chart-controls">
                  <label>
                    Partisipan&nbsp;
                    <select
                      value={participant}
                      onChange={(event) =>
                        setParticipant(event.target.value)
                      }
                    >
                      <option>
                        Semua Partisipan
                      </option>

                      {meta?.participants?.map(
                        (id) => (
                          <option key={id}>
                            {id}
                          </option>
                        )
                      )}
                    </select>
                  </label>
                </div>

                <TrendPlot
                  trends={
                    participant === "Semua Partisipan"
                      ? summary.trends
                      : single
                  }
                />
              </Card>

              <Card title="Distribusi Tekanan Darah">
                <Donut
                  distribution={summary.distribution}
                  total={summary.total_participants}
                />

                <DistributionLegend
                  distribution={summary.distribution}
                />
              </Card>
            </div>

            {/* Analisis usia dan korelasi */}
            <div className="dashboard-row dashboard-row-two">
              <Card title="Distribusi Tekanan Darah Berdasarkan Usia">
                <AgeBars items={summary.by_age} />
              </Card>

              <Card title="Hubungan Faktor Risiko dengan Tekanan Darah">
                <CorrHeatmap
                  items={summary.correlations}
                />
              </Card>
            </div>

            {/* Model dan tabel partisipan */}
            <div className="dashboard-row dashboard-row-three">
              <Card
                title="Prediksi Hipertensi (Klasifikasi)"
                icon={Target}
                className="model-card"
              >
                {model ? (
                  <>
                    <span className="demo-inline">
                      DATA CONTOH · BUKAN MODEL TERLATIH
                    </span>

                    <ModelDonut
                      accuracy={model.akurasi}
                    />

                    <Confusion
                      matrix={model.confusion_matrix}
                    />
                  </>
                ) : (
                  <Notice tone="warning">
                    Data evaluasi model demo belum
                    tersedia. Model ML belum dilatih.
                  </Notice>
                )}
              </Card>

              <Card
                title="Performa Model"
                icon={ChartColumn}
              >
                {model ? (
                  <>
                    <span className="demo-inline">
                      CONTOH
                    </span>

                    <ModelBars
                      models={model.models}
                    />
                  </>
                ) : (
                  <Notice tone="warning">
                    Performa model belum dapat
                    ditampilkan.
                  </Notice>
                )}
              </Card>

              <Card
                title="Data Partisipan (Contoh)"
                icon={TableProperties}
              >
                <div className="table-scroll">
                  <table className="mini-table">
                    <thead>
                      <tr>
                        <th>ID Partisipan</th>
                        <th>Usia</th>
                        <th>Jenis Kelamin</th>
                        <th>Kecamatan</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {summary.samples?.map(
                        (row) => (
                          <tr key={row.id_partisipan}>
                            <td>
                              {row.id_partisipan}
                            </td>

                            <td>{row.usia}</td>

                            <td>
                              {row.jenis_kelamin}
                            </td>

                            <td>
                              {row.kecamatan}
                            </td>

                            <td>
                              <Status
                                status={
                                  row.status_hipertensi
                                }
                              />
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>

                <button
                  type="button"
                  className="link-button"
                  onClick={() =>
                    changePage("Data Partisipan")
                  }
                >
                  Lihat semua data
                  <ArrowRight size={15} />
                </button>
              </Card>
            </div>
          </>
        )}
      </div>

      {/* Filter samping dashboard */}
      <div className="dashboard-side">
        <FilterPanel
          filters={filters}
          setFilters={setFilters}
          meta={meta}
          summary={summary}
        />
      </div>
    </div>
  );
}
