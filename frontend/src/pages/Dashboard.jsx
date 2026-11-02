import React, {useEffect, useState} from 'react';
import { AlertTriangle, Activity, HeartPulse, Target, UsersRound, ChartColumn, TableProperties, ArrowRight, SlidersHorizontal } from 'lucide-react';
import { Card, PlotlyChart, Status, Empty, Notice } from '../components/Common';
import { FilterPanel } from '../components/Filters';
import { AgeBars, CorrHeatmap, Confusion, DistributionLegend, Donut, ModelBars, ModelDonut, TrendPlot } from '../components/Charts';
import { api, queryString, fmt, whole } from '../lib/api';

function KPI({tone,Icon,label,value,sub}){return <div className={'kpi kpi-'+tone}><div className="kpi-ico"><Icon size={23}/></div><div className="kpi-content"><div className="kpi-label">{label}</div><div className="kpi-value">{value}</div><div className="kpi-sub">{sub}</div></div></div>}

export default function Dashboard({summary,meta,filters,setFilters,model,changePage}){
 const [participant,setParticipant]=useState('Semua Partisipan');const [single,setSingle]=useState([]);
 useEffect(()=>{if(participant==='Semua Partisipan'){setSingle([]);return;}let live=true;api('/measurements'+queryString(filters,{id_partisipan:participant,page_size:1000})).then(r=>{if(live)setSingle(r.rows.map(x=>({tanggal:x.tanggal,sistolik_mean:x.sistolik,diastolik_mean:x.diastolik})));}).catch(()=>{});return()=>{live=false}},[participant,JSON.stringify(filters)]);
 useEffect(()=>{setParticipant('Semua Partisipan')},[JSON.stringify(filters)]);
 return <div className="dashboard-layout"><div className="dashboard-content">
  {summary?.empty?<Empty/>:<>
    <div className="kpi-grid">
      <KPI tone="biru" Icon={UsersRound} label="Jumlah Partisipan" value={whole(summary.total_participants)} sub="Usia produktif (15–64 tahun)"/>
      <KPI tone="hijau" Icon={HeartPulse} label="Total Pengukuran" value={whole(summary.total_rows)} sub={`Data selama ${summary.days} hari`}/>
      <KPI tone="merah" Icon={AlertTriangle} label="Di Atas Rentang Normal" value={<>{summary.non_normal}<small className="kpi-pct">({fmt(summary.non_normal_percent,0)}%)</small></>} sub="Pra-hipertensi + Hipertensi"/>
      <KPI tone="ungu" Icon={Activity} label="Rata-rata Tekanan Darah" value={<>{fmt(summary.mean_sistolik,0)}/{fmt(summary.mean_diastolik,0)}<small>mmHg</small></>} sub="Sistolik / Diastolik"/>
    </div>
    <div className="dashboard-row dashboard-row-one">
      <Card title="Tren Tekanan Darah Rata-rata"><div className="chart-controls"><label>Partisipan&nbsp; <select value={participant} onChange={e=>setParticipant(e.target.value)}><option>Semua Partisipan</option>{meta?.participants?.map(x=><option key={x}>{x}</option>)}</select></label></div><TrendPlot trends={participant==='Semua Partisipan'?summary.trends:single} /></Card>
      <Card title="Distribusi Tekanan Darah"><Donut distribution={summary.distribution} total={summary.total_participants}/><DistributionLegend distribution={summary.distribution}/></Card>
    </div>
    <div className="dashboard-row dashboard-row-two">
      <Card title="Distribusi Tekanan Darah Berdasarkan Usia"><AgeBars items={summary.by_age}/></Card>
      <Card title="Hubungan Faktor Risiko dengan Tekanan Darah"><CorrHeatmap items={summary.correlations}/></Card>
    </div>
    <div className="dashboard-row dashboard-row-three">
      <Card title="Prediksi Hipertensi (Klasifikasi)" icon={Target} className="model-card"><span className="demo-inline">DATA CONTOH · BUKAN MODEL TERLATIH</span><ModelDonut accuracy={model.akurasi}/><Confusion matrix={model.confusion_matrix}/></Card>
      <Card title="Performa Model" icon={ChartColumn}><span className="demo-inline">CONTOH</span><ModelBars models={model.models}/></Card>
      <Card title="Data Partisipan (Contoh)" icon={TableProperties}><div className="table-scroll"><table className="mini-table"><thead><tr><th>ID Partisipan</th><th>Usia</th><th>Jenis Kelamin</th><th>Kecamatan</th><th>Status</th></tr></thead><tbody>{summary.samples?.map(x=><tr key={x.id_partisipan}><td>{x.id_partisipan}</td><td>{x.usia}</td><td>{x.jenis_kelamin}</td><td>{x.kecamatan}</td><td><Status status={x.status_hipertensi}/></td></tr>)}</tbody></table></div><button className="link-button" onClick={()=>changePage('Data Partisipan')}>Lihat semua data <ArrowRight size={15}/></button></Card>
    </div>
   </>}
 </div><div className="dashboard-side"><FilterPanel filters={filters} setFilters={setFilters} meta={meta} summary={summary}/></div></div>;
}
