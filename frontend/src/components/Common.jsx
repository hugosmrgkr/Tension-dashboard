import React from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import {Activity, CalendarDays, ChartColumn, ChartNoAxesCombined, ClipboardList, Database, HeartPulse, House, Menu, ShieldAlert, SlidersHorizontal, Target, UsersRound, X, AlertTriangle, RefreshCcw} from 'lucide-react';
import {dateID} from '../lib/api';
const Plot=createPlotlyComponent(Plotly);
export const NAV=[['Dashboard',House],['Data Partisipan',UsersRound],['Analisis Faktor Risiko',ChartColumn],['Tren Tekanan Darah',ChartNoAxesCombined],['Prediksi Hipertensi',Target],['Evaluasi Model',Activity],['Laporan & Ringkasan',ClipboardList],['Kelola Data',Database]];
export const INFO={
 'Dashboard':'Gambaran umum pengukuran pagi dan malam dari dataset yang sedang dipilih.',
 'Data Partisipan':'Profil responden dengan ID pseudonim dan jumlah catatan harian.',
 'Analisis Faktor Risiko':'Eksplorasi hubungan faktor gaya hidup dengan tekanan darah — bukan sebab-akibat.',
 'Tren Tekanan Darah':'Bandingkan pola sistolik dan diastolik sesi pagi serta malam.',
 'Prediksi Hipertensi':'Eksperimen baseline: perkiraan rata-rata sistolik 7 hari berikutnya (bukan diagnosis).',
 'Evaluasi Model':'Metrik baseline dan pembanding pada data sintetis, tanpa klaim klinis.',
 'Laporan & Ringkasan':'Lima temuan deskriptif, ukuran sampel, dan batas interpretasi.',
 'Kelola Data':'Sumber, pemeriksaan kualitas data, unduh CSV, serta impor terproteksi.'
};
export function Sidebar({page,changePage,isOpen,setOpen}){return <>{isOpen&&<div className="sidebar-backdrop" onClick={()=>setOpen(false)}/>}<aside className={'sidebar '+(isOpen?'open':'')}><div className="brand"><img src="/logo.svg" className="brand-logo" alt="Logo"/><div><div className="brand-name">Toba Health Insight</div><div className="brand-tag">Dasbor Pengukuran Tekanan Darah</div></div></div><nav className="nav-list" aria-label="Navigasi halaman">{NAV.map(([label,Icon])=><button key={label} type="button" className={'nav-item '+(page===label?'active':'')} onClick={()=>{changePage(label);setOpen(false)}}><Icon size={17}/><span>{label}</span></button>)}</nav><div className="side-bottom"><div className="side-note"><span>Proyek DALIS + DASI<br/>Checkpoint M6–M8<br/>Data simulasi, bukan diagnosis medis</span></div><img src="/danau-toba.svg" alt="Ilustrasi Danau Toba"/></div></aside></>}
export function Header({page,meta,setOpen}){return <header className="app-header"><div className="heading"><button className="mobile-menu icon-button" aria-label="Buka navigasi" onClick={()=>setOpen(true)}><Menu size={21}/></button><div><h1>{page}</h1><p>{INFO[page]}</p></div></div><div className="header-right"><span className={'data-mode '+(meta?.source_kind==='synthetic'?'synthetic':'actual')}>{meta?.source_kind==='synthetic'?'DATA SINTETIS / SIMULASI':'SUMBER DATA TERBATAS'}</span><div className="pill-date"><CalendarDays size={15}/>{dateID(meta?.min_date)} – {dateID(meta?.max_date)}</div></div></header>}
export function Footer({meta}){return <footer className="app-footer"><span>© 2026 Toba Health Insight · Eksplorasi akademik, bukan panduan medis</span><span><RefreshCcw size={13}/>Sumber: {meta?.source||'Memuat...'}</span></footer>}
export function Card({title,icon:Icon,children,className='',action}){return <section className={'card '+className}><div className="card-heading"><h2>{Icon&&<Icon size={17}/>} {title}</h2>{action}</div>{children}</section>}
export function Notice({children,tone='info'}){const Icon=tone==='warning'?ShieldAlert:tone==='error'?AlertTriangle:SlidersHorizontal;return <div className={'notice notice-'+tone} role={tone==='error'?'alert':'note'}><Icon size={17}/><div>{children}</div></div>}
export function Loading(){return <div className="loading" role="status">Mengambil data dari FastAPI dan PostgreSQL…</div>}
export function Empty(){return <Notice tone="warning">Tidak ada data pada pilihan filter ini. Coba ubah rentang tanggal atau filter lainnya.</Notice>}
const font={family:'Inter, Segoe UI, sans-serif',size:11,color:'#5b6b88'};
export function PlotlyChart({data=[],layout={},height=310}){return <div className="plot-wrap"><Plot data={data} useResizeHandler style={{width:'100%',height}} config={{displaylogo:false,responsive:true,modeBarButtonsToRemove:['lasso2d','select2d']}} layout={{height,autosize:true,margin:{l:52,r:18,t:20,b:55},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font,hovermode:'closest',hoverlabel:{bgcolor:'#172954',font:{color:'#fff',size:12}},xaxis:{gridcolor:'#edf1f7',automargin:true},yaxis:{gridcolor:'#edf1f7',automargin:true},legend:{orientation:'h',y:-.23},...layout}}/></div>}
export function MiniTable({columns,rows,empty='Tidak ada data.'}){return <div className="table-scroll"><table className="data-table"><thead><tr>{columns.map(([key,label])=><th key={key}>{label}</th>)}</tr></thead><tbody>{rows.length?rows.map((r,i)=><tr key={i}>{columns.map(([key])=><td key={key}>{r[key]??'–'}</td>)}</tr>):<tr><td colSpan={columns.length}>{empty}</td></tr>}</tbody></table></div>}
