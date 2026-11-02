import React, { useEffect, useState } from 'react';
import { api, queryString } from './lib/api';
import { Header, Sidebar, Footer, Loading, Notice } from './components/Common';
import { FilterPanel, initialFilters } from './components/Filters';
import Dashboard from './pages/Dashboard';
import { DataPartisipan, FaktorRisiko, Tren, Prediksi, Evaluasi, Laporan, KelolaData } from './pages/OtherPages';

const pages=['Dashboard','Data Partisipan','Analisis Faktor Risiko','Tren Tekanan Darah','Prediksi Hipertensi','Evaluasi Model','Laporan & Ringkasan','Kelola Data'];
const pageFromHash=()=>pages.includes(decodeURIComponent(location.hash.substring(1)))?decodeURIComponent(location.hash.substring(1)):'Dashboard';

export default function App(){
 const [page,setPage]=useState(pageFromHash);const [mobileOpen,setMobileOpen]=useState(false);
 const [meta,setMeta]=useState(null),[summary,setSummary]=useState(null),[model,setModel]=useState(null);
 const [filters,setFilters]=useState({...initialFilters});const [revision,setRevision]=useState(0),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const changePage=(name)=>{setPage(name);location.hash=encodeURIComponent(name);window.scrollTo({top:0,behavior:'smooth'});};
 useEffect(()=>{const handler=()=>setPage(pageFromHash());window.addEventListener('hashchange',handler);return()=>window.removeEventListener('hashchange',handler)},[]);
 async function refresh(){setRevision(n=>n+1);const data=await api('/meta');setMeta(data);}
 useEffect(()=>{api('/model/demo').then(setModel).catch(e=>setError(e.message));refresh().catch(e=>{setError(e.message);setLoading(false)});},[]);
 useEffect(()=>{if(!meta)return;let live=true;setLoading(true);setError('');api('/analytics'+queryString(filters)).then(data=>{if(live){setSummary(data);setLoading(false)}}).catch(e=>{if(live){setError(e.message);setLoading(false)}});return()=>{live=false}},[meta,JSON.stringify(filters),revision]);
 let content=null;
 if(!loading&&summary&&model){switch(page){
  case 'Dashboard':content=<Dashboard summary={summary} filters={filters} setFilters={setFilters} meta={meta} model={model} changePage={changePage}/>;break;
  case 'Data Partisipan':content=<DataPartisipan filters={filters} revision={revision}/>;break;
  case 'Analisis Faktor Risiko':content=<FaktorRisiko summary={summary}/>;break;
  case 'Tren Tekanan Darah':content=<Tren summary={summary}/>;break;
  case 'Prediksi Hipertensi':content=<Prediksi summary={summary}/>;break;
  case 'Evaluasi Model':content=<Evaluasi model={model}/>;break;
  case 'Laporan & Ringkasan':content=<Laporan summary={summary} filters={filters}/>;break;
  case 'Kelola Data':content=<KelolaData meta={meta} filters={filters} revision={revision} refresh={refresh}/>;break;
  default:content=null;
 }}
 return <div className="app-shell"><Sidebar page={page} changePage={changePage} isOpen={mobileOpen} setOpen={setMobileOpen}/><main className="main-area"><Header page={page} meta={meta} setOpen={setMobileOpen}/>{page!=='Dashboard'&&<details className="global-filter"><summary>Filter Global (berlaku untuk semua analisis dan tabel)</summary><FilterPanel filters={filters} setFilters={setFilters} meta={meta} summary={null}/></details>}{error&&<Notice tone="error">Gagal menghubungi API: {error}. Pastikan backend FastAPI aktif.</Notice>}{loading?<Loading/>:content}<Footer meta={meta}/></main></div>;
}
