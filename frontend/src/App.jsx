
import React, { useEffect, useState } from "react";
import { api, queryString } from "./lib/api";
import {
  Header,
  Sidebar,
  Footer,
  Loading,
  Notice,
} from "./components/Common";
import { FilterPanel, initialFilters } from "./components/Filters";
import Dashboard from "./pages/Dashboard";
import {
  DataPartisipan,
  FaktorRisiko,
  Tren,
  Prediksi,
  Evaluasi,
  Laporan,
  KelolaData,
} from "./pages/OtherPages";

const pages = [
  "Dashboard",
  "Data Partisipan",
  "Analisis Faktor Risiko",
  "Tren Tekanan Darah",
  "Prediksi Hipertensi",
  "Evaluasi Model",
  "Laporan & Ringkasan",
  "Kelola Data",
];

const pageFromHash = () => {
  const hash = decodeURIComponent(location.hash.substring(1));
  return pages.includes(hash) ? hash : "Dashboard";
};

export default function App() {
  const [page, setPage] = useState(pageFromHash);
  const [mobileOpen, setMobileOpen] = useState(false);

  const [meta, setMeta] = useState(null);
  const [summary, setSummary] = useState(null);
  const [model, setModel] = useState(null);
  const [modelError, setModelError] = useState("");

  const [filters, setFilters] = useState({ ...initialFilters });
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const changePage = (name) => {
    setPage(name);
    location.hash = encodeURIComponent(name);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handler = () => setPage(pageFromHash());
    window.addEventListener("hashchange", handler);

    return () => window.removeEventListener("hashchange", handler);
  }, []);

  async function refresh() {
    setRevision((n) => n + 1);
    const data = await api("/meta");
    setMeta(data);
  }

  async function loadModel() {
    try {
      setModelError("");
      const data = await api("/model/demo");
      setModel(data);
    } catch (e) {
      setModel(null);
      setModelError(e.message);
    }
  }

  useEffect(() => {
    loadModel();

    refresh().catch((e) => {
      setError(e.message);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!meta) return;

    let live = true;

    setLoading(true);
    setError("");

    api("/analytics" + queryString(filters))
      .then((data) => {
        if (live) {
          setSummary(data);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (live) {
          setSummary(null);
          setError(e.message);
          setLoading(false);
        }
      });

    return () => {
      live = false;
    };
  }, [meta, JSON.stringify(filters), revision]);

  let content = null;
  const requiresAnalytics = [
    "Dashboard", "Analisis Faktor Risiko", "Tren Tekanan Darah", "Laporan & Ringkasan",
  ].includes(page);

  // Pengelolaan data dan prediksi tetap tersedia saat analitik gagal.
  if (!requiresAnalytics || (!loading && summary)) {
    switch (page) {
      case "Dashboard":
        content = (
          <Dashboard
            summary={summary}
            filters={filters}
            setFilters={setFilters}
            meta={meta}
            model={model}
            changePage={changePage}
          />
        );
        break;

      case "Data Partisipan":
        content = (
          <DataPartisipan
            filters={filters}
            revision={revision}
          />
        );
        break;

      case "Analisis Faktor Risiko":
        content = <FaktorRisiko summary={summary} />;
        break;

      case "Tren Tekanan Darah":
        content = <Tren summary={summary} />;
        break;

      case "Prediksi Hipertensi":
        content = <Prediksi summary={summary} />;
        break;

      case "Evaluasi Model":
        content = <Evaluasi model={model} />;
        break;

      case "Laporan & Ringkasan":
        content = (
          <Laporan summary={summary} filters={filters} />
        );
        break;

      case "Kelola Data":
        content = (
          <KelolaData
            meta={meta}
            filters={filters}
            revision={revision}
            refresh={refresh}
          />
        );
        break;

      default:
        content = null;
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        changePage={changePage}
        isOpen={mobileOpen}
        setOpen={setMobileOpen}
      />

      <main className="main-area">
        <Header
          page={page}
          meta={meta}
          setOpen={setMobileOpen}
        />

        {page !== "Dashboard" && (
          <details className="global-filter">
            <summary>
              Filter Global (berlaku untuk semua analisis dan tabel)
            </summary>
            <FilterPanel
              filters={filters}
              setFilters={setFilters}
              meta={meta}
              summary={null}
            />
          </details>
        )}

        {error && (
          <Notice tone="error">
            Gagal memuat data analitik: {error}.
            Periksa endpoint /api/analytics dan log backend.
          </Notice>
        )}

        {modelError && (
          <Notice tone="warning">
            Data evaluasi model demo gagal dimuat: {modelError}.
            Dashboard tetap dapat digunakan.
            <button
              type="button"
              className="link-button"
              onClick={loadModel}
            >
              Coba lagi
            </button>
          </Notice>
        )}

        {loading && requiresAnalytics ? <Loading /> : content}

        {requiresAnalytics && !loading && !summary && !error && (
          <Notice tone="warning">
            Data analitik belum tersedia.
            Periksa endpoint /api/analytics.
          </Notice>
        )}

        <Footer meta={meta} />
      </main>
    </div>
  );
}
