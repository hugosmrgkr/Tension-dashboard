import React from 'react';
import { Filter, RotateCcw, Moon, UsersRound, Gauge, Zap, AlertTriangle } from 'lucide-react';
import { Card, Select, Input } from './Common';
import { fmt } from '../lib/api';

export const initialFilters = {awal:'',akhir:'',kecamatan:'',jenis_kelamin:'',kelompok_usia:'',id_partisipan:''};

export function FilterPanel({filters, setFilters, meta, summary}){
 const update=(key,value)=>setFilters(prev=>({...prev,[key]:value}));
 return <div className="right-panels">
  <Card title="Filter Data" icon={Filter} className="filter-card" action={<button className="text-button" title="Reset filter" onClick={()=>setFilters({...initialFilters})}><RotateCcw size={14}/></button>}>
    <div className="filter-grid"><div className="field"><span>Tanggal</span><div className="date-pair"><input type="date" min={meta?.min_date??undefined} max={meta?.max_date??undefined} value={filters.awal||meta?.min_date||''} onChange={e=>update('awal',e.target.value)}/><input type="date" min={meta?.min_date??undefined} max={meta?.max_date??undefined} value={filters.akhir||meta?.max_date||''} onChange={e=>update('akhir',e.target.value)}/></div></div>
    <Select label="Kecamatan" value={filters.kecamatan} onChange={v=>update('kecamatan',v)} options={[{value:'',label:'Semua Kecamatan'},...(meta?.kecamatan??[])]}/>
    <Select label="Jenis Kelamin" value={filters.jenis_kelamin} onChange={v=>update('jenis_kelamin',v)} options={[{value:'',label:'Semua'},...(meta?.jenis_kelamin??[])]}/>
    <Select label="Kelompok Usia" value={filters.kelompok_usia} onChange={v=>update('kelompok_usia',v)} options={[{value:'',label:'Semua'},...(meta?.kelompok_usia??[])]}/>
    <Input label="ID Partisipan" placeholder="Cari ID partisipan..." value={filters.id_partisipan} onChange={e=>update('id_partisipan',e.target.value)} />
    </div>
  </Card>
  {summary && !summary.empty && <>
    <Card title="Ringkasan Statistik" className="summary-card"><div className="summary-list">
      <div className="stat"><span><UsersRound size={15}/>Rata-rata Usia</span><b>{fmt(summary.mean_usia)} tahun</b></div>
      <div className="stat"><span><Gauge size={15}/>Rata-rata BMI</span><b>{fmt(summary.mean_bmi)} kg/m²</b></div>
      <div className="stat"><span><Zap size={15}/>Rata-rata Aktivitas Fisik</span><b>{fmt(summary.mean_aktivitas)} hari/minggu</b></div>
      <div className="stat"><span><Moon size={15}/>Rata-rata Durasi Tidur</span><b>{fmt(summary.mean_tidur)} jam</b></div>
    </div></Card>
    <section className="risk-box"><h3><AlertTriangle size={17}/> Faktor Risiko Utama</h3>{summary.risk_factors?.map((r,i)=><div className="risk-row" key={r.label}><span>{i+1}. {r.label}</span><b>({fmt(r.percent,0)}%)</b></div>)}</section>
  </>}
 </div>;
}
