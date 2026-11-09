import React,{useEffect,useState} from 'react';
import {Sidebar,Header,Footer,Notice,Loading,NAV} from './components/Common';
import FilterBar from './components/FilterBar';
import {Dashboard,DataPartisipan,FaktorRisiko,Tren,Prediksi,Evaluasi,Laporan,KelolaData} from './pages/Pages';
import {api,queryString} from './lib/api';
const pages=NAV.map(x=>x[0]);
const getPage=()=>{try{const hash=decodeURIComponent(window.location.hash.slice(1));return pages.includes(hash)?hash:'Dashboard'}catch{return 'Dashboard'}};
export default function App(){
 const [page,setPage]=useState(getPage);const [menu,setMenu]=useState(false);const [meta,setMeta]=useState(null);
 const [data,setData]=useState(null);const [model,setModel]=useState(null);const [filters,setFilters]=useState({});
 const [error,setError]=useState('');const [loading,setLoading]=useState(true);const [revision,setRevision]=useState(0);
 const key=JSON.stringify(filters);
 const go=name=>{setPage(name);window.location.hash=encodeURIComponent(name);window.scrollTo({top:0,behavior:'smooth'})};
 useEffect(()=>{const handler=()=>setPage(getPage());window.addEventListener('hashchange',handler);return ()=>window.removeEventListener('hashchange',handler)},[]);
 const reload=async()=>{const m=await api('/meta');setMeta(m);setRevision(x=>x+1)};
 useEffect(()=>{reload().catch(e=>{setError(e.message);setLoading(false)});api('/model/baseline').then(setModel).catch(e=>console.error('Baseline metric:',e))},[]);
 useEffect(()=>{if(!meta)return;let active=true;setLoading(true);setError('');api('/analytics'+queryString(JSON.parse(key))).then(d=>{if(active){setData(d);setLoading(false)}}).catch(e=>{if(active){setData(null);setError(e.message);setLoading(false)}});return ()=>{active=false}},[meta,revision,key]);
 const current=()=>{switch(page){case'Dashboard':return <Dashboard data={data} go={go}/>;case'Data Partisipan':return <DataPartisipan data={data}/>;case'Analisis Faktor Risiko':return <FaktorRisiko data={data}/>;case'Tren Tekanan Darah':return <Tren data={data}/>;case'Prediksi Hipertensi':return <Prediksi meta={meta} model={model}/>;case'Evaluasi Model':return <Evaluasi model={model}/>;case'Laporan & Ringkasan':return <Laporan data={data} go={go}/>;case'Kelola Data':return <KelolaData meta={meta} data={data} reload={reload}/>;default:return null}};
 return <div className="app-shell"><Sidebar page={page} changePage={go} isOpen={menu} setOpen={setMenu}/><main className="main-area"><Header page={page} meta={meta} setOpen={setMenu}/>{meta&&<FilterBar meta={meta} filters={filters} setFilters={setFilters}/>}<div className="source-banner"><b>{meta?.source_kind==='synthetic'?'DATA SINTETIS / SIMULASI':'DATA TERBATAS'}</b><span>{meta?.source_kind==='synthetic'?'Dataset buatan untuk pengembangan, bukan penelitian atau diagnosis.':'Data diunggah membutuhkan izin, validasi kualitas, dan akses terbatas.'}</span></div>{error&&<Notice tone="error">Gagal memuat data: {error}. Cek FastAPI di <code>/api/analytics</code>.</Notice>}{loading?<Loading/>:data?current():<Notice tone="warning">Tidak ada data yang dapat ditampilkan.</Notice>}<Footer meta={meta}/></main></div>
}
