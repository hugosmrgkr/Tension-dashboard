import React from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
const Plot = createPlotlyComponent(Plotly);
import { AlertTriangle, Activity, CalendarDays, ChartColumn, ChartNoAxesCombined, ChevronDown, ClipboardList, Database, HeartPulse, House, Menu, RefreshCcw, ShieldAlert, SlidersHorizontal, Target, UsersRound, X } from 'lucide-react';
import { dateID } from '../lib/api';

export const NAV = [
 ['Dashboard', House], ['Data Partisipan', UsersRound], ['Analisis Faktor Risiko', ChartColumn],
 ['Tren Tekanan Darah', ChartNoAxesCombined], ['Prediksi Hipertensi', Target], ['Evaluasi Model', Activity],
 ['Laporan & Ringkasan', ClipboardList], ['Kelola Data', Database]
];

export const INFO = {
  'Dashboard':'Ringkasan data tekanan darah dan kejadian hipertensi pada masyarakat usia produktif di Kabupaten Toba',
  'Data Partisipan':'Seluruh data pengukuran tekanan darah partisipan.',
  'Analisis Faktor Risiko':'Eksplorasi deskriptif faktor risiko. Hubungan statistik bukan bukti sebab-akibat.',
  'Tren Tekanan Darah':'Pergerakan harian rata-rata dan rentang tekanan darah.',
  'Prediksi Hipertensi':'Alur input dan keluaran klasifikasi untuk dataset final.',
  'Evaluasi Model':'Perbandingan performa model klasifikasi.',
  'Laporan & Ringkasan':'Ringkasan data yang sedang dianalisis.',
  'Kelola Data':'Sumber data, penyuntingan, dan ekspor.'
};

export function Sidebar({ page, changePage, isOpen, setOpen }) {
  return <>
    {isOpen && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}
    <aside className={'sidebar ' + (isOpen ? 'open' : '')}>
      <div className="brand"><img src="/logo.svg" className="brand-logo" alt="Logo Toba Health Insight"/><div><div className="brand-name">Toba Health Insight</div><div className="brand-tag">Sehat Hari Ini, Masa Depan Lebih Baik</div></div></div>
      <nav className="nav-list" aria-label="Navigasi utama">
        {NAV.map(([label, Icon]) => <button key={label} className={'nav-item ' + (page === label ? 'active' : '')} onClick={() => { changePage(label); setOpen(false); }}><Icon size={18}/><span>{label}</span></button>)}
      </nav>
      <div className="side-bottom"><div className="side-note"><div className="side-note-ico"><UsersRound size={15}/></div><span>Analisis Faktor Risiko dan Prediksi Hipertensi pada Masyarakat Usia Produktif di Kabupaten Toba</span></div><img src="/danau-toba.svg" alt="Ilustrasi Danau Toba"/></div>
    </aside>
  </>;
}

export function Header({ page, meta, setOpen }) {
  return <header className="app-header">
    <div className="heading"><button className="mobile-menu icon-button" onClick={() => setOpen(true)} aria-label="Buka menu"><Menu/></button><div><h1>{page}</h1><p>{INFO[page]}</p></div></div>
    <div className="header-right"><div className="header-controls"><div className="region-box">Kabupaten Toba <ChevronDown size={14}/></div><div className="chip-user"><div className="avatar"><UsersRound size={14}/></div> User <ChevronDown size={14}/></div></div><div className="pill-date"><CalendarDays size={15}/>{dateID(meta?.min_date)} – {dateID(meta?.max_date)}</div></div>
  </header>;
}

export function Footer({ meta }) { return <footer className="app-footer"><span>© 2025 Toba Health Insight &nbsp;|&nbsp; Analisis Faktor Risiko dan Prediksi Hipertensi</span><span><RefreshCcw size={13}/> Periode terakhir: {dateID(meta?.max_date)}</span></footer>; }

export function Card({ title, icon: Icon, children, className = '', action, style }) {
 return <section className={'card ' + className} style={style}>{title && <div className="card-heading"><h2>{Icon && <Icon size={17}/>} {title}</h2>{action}</div>}{children}</section>;
}

export function Badge({ children, tone='neutral' }) {return <span className={'tag tag-' + tone}>{children}</span>;}
export function Notice({ children, tone = 'info' }) {const Icon = tone === 'warning' ? ShieldAlert : tone === 'error' ? AlertTriangle : SlidersHorizontal; return <div className={'notice notice-' + tone}><Icon size={17}/><span>{children}</span></div>;}
export function Loading() {return <div className="loading">Memuat data dashboard…</div>;}
export function Empty() {return <Notice tone="warning">Tidak ada data yang cocok dengan filter. Ubah filter untuk melihat grafik.</Notice>;}

const font = { family: 'Inter, sans-serif', size: 11, color: '#5b6b88' };
export function PlotlyChart({ data, layout={}, height=250, className = '' }) {
 return <div className={'plot-wrap ' + className}><Plot data={data} useResizeHandler style={{width:'100%',height:height}} config={{displayModeBar:false,responsive:true}} layout={{height,margin:{l:30,r:12,t:14,b:40},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font,hoverlabel:{bgcolor:'#15264b',font:{color:'white',size:12}},xaxis:{gridcolor:'#edf1f7',linecolor:'#dfe6f1',zeroline:false,automargin:true},yaxis:{gridcolor:'#edf1f7',zeroline:false,automargin:true},...layout}} /></div>;
}

export function Status({ status }) {const cls = status === 'Normal' ? 'ok' : status === 'Pra-hipertensi' ? 'warn' : 'danger';return <span className={'status status-'+cls}>{status}</span>}
export function Select({label, value, onChange, options, className = ''}){return <label className={'field '+className}><span>{label}</span><select value={value} onChange={e=>onChange(e.target.value)}>{options.map(x=><option key={x.value??x} value={x.value??x}>{x.label??x}</option>)}</select></label>}
export function Input({label, ...props}){return <label className="field"><span>{label}</span><input {...props}/></label>}
