import React, {useEffect, useState} from 'react';
import {Sidebar, Header, Footer, Notice, Loading, Empty, NAV} from './components/Common';
import FilterBar from './components/FilterBar';
import {Dashboard, DataPartisipan, FaktorRisiko, Tren, Prediksi, Evaluasi, Laporan, KelolaData} from './pages/Pages';
import {api,queryString,setToken} from './lib/api';

const pages=NAV.map(item=>item[0]);
const getPage=()=>{try{const hash=decodeURIComponent(window.location.hash.slice(1));return pages.includes(hash)?hash:'Dashboard'}catch{return 'Dashboard'}};

export default function App(){
  const [page,setPage]=useState(getPage), [menu,setMenu]=useState(false);
  const [meta,setMeta]=useState(null), [data,setData]=useState(null), [filters,setFilters]=useState({});
  const [authRequired,setAuthRequired]=useState(false), [tokenInput,setTokenInput]=useState('');
  const [error,setError]=useState(''), [loading,setLoading]=useState(true), [revision,setRevision]=useState(0);
  const [model,setModel]=useState(null), [modelError,setModelError]=useState(''), [modelRevision,setModelRevision]=useState(0);
  const [modelLoading,setModelLoading]=useState(false);
  const [comparison,setComparison]=useState(null), [comparisonLoading,setComparisonLoading]=useState(false);
  const filterKey=JSON.stringify(filters);
  const baselinePage=['Prediksi Tekanan Darah','Evaluasi Model'].includes(page);
  const independent=baselinePage || page==='Kelola Data';
  const reload=()=>setRevision(value=>value+1);
  const crossFilter=values=>setFilters(old=>({...old,...values,...('province' in values&&!('city' in values)?{city:''}:{})}));
  const go=name=>{setPage(name);window.location.hash=encodeURIComponent(name);window.scrollTo({top:0,behavior:'smooth'})};

  useEffect(()=>{
    const handler=()=>setPage(getPage());
    window.addEventListener('hashchange',handler);
    return ()=>window.removeEventListener('hashchange',handler);
  },[]);

  useEffect(()=>{
    const controller=new AbortController();let active=true;
    setLoading(true);setError('');setData(null);
    if(filters.start_date&&filters.end_date&&filters.start_date>filters.end_date){
      setError('Tanggal mulai harus sebelum atau sama dengan tanggal sampai. Perbaiki filter tanggal.');setLoading(false);
      return ()=>{active=false;controller.abort()};
    }
    (async()=>{
      try{
        const next=await api('/meta',{signal:controller.signal});
        if(!active)return;
        setMeta(next);
        if(next.access_restricted)return;
        const result=await api('/analytics'+queryString(JSON.parse(filterKey)),{signal:controller.signal});
        if(active)setData(result);
      }catch(err){
        if(active && err.status===401){setAuthRequired(true);setToken('');}
        else if(active && err.name!=='AbortError')setError(err.message);
      }finally{if(active)setLoading(false)}
    })();
    return ()=>{active=false;controller.abort()};
  },[filterKey,revision]);

  useEffect(()=>{
    const controller=new AbortController();let active=true;
    setModel(null);setModelError('');setModelLoading(false);
    if(!meta || meta.warehouse_empty || meta.access_restricted || meta.source_kind!=='synthetic')return;
    setModelLoading(true);
    api('/model/baseline',{signal:controller.signal}).then(result=>{if(active)setModel(result)}).catch(err=>{
      if(active && err.name!=='AbortError')setModelError(err.message);
    }).finally(()=>{if(active)setModelLoading(false)});
    return ()=>{active=false;controller.abort()};
  },[meta?.source_kind,meta?.warehouse_empty,meta?.access_restricted,meta?.data_version,revision,modelRevision]);

  useEffect(()=>{
    const controller=new AbortController();let active=true;
    setComparison(null);setComparisonLoading(false);
    if(!meta || meta.warehouse_empty || meta.access_restricted || meta.source_kind!=='synthetic')return;
    setComparisonLoading(true);
    api('/model/comparison',{signal:controller.signal}).then(result=>{if(active)setComparison(result)}).catch(err=>{
      if(active && err.name!=='AbortError')setComparison({available:false,message:'Perbandingan model belum dapat dimuat: '+err.message});
    }).finally(()=>{if(active)setComparisonLoading(false)});
    return ()=>{active=false;controller.abort()};
  },[meta?.source_kind,meta?.warehouse_empty,meta?.access_restricted,meta?.data_version,revision,modelRevision]);

  function current(){
    switch(page){
      case 'Dashboard':return <Dashboard data={data} go={go} onFilter={crossFilter}/>;
      case 'Data Partisipan':return <DataPartisipan data={data} onFilter={crossFilter}/>;
      case 'Analisis Faktor Risiko':return <FaktorRisiko data={data} onFilter={crossFilter}/>;
      case 'Tren Tekanan Darah':return <Tren data={data} filters={filters} onFilter={crossFilter}/>;
      case 'Prediksi Tekanan Darah':return <Prediksi meta={meta} model={comparison} modelLoading={comparisonLoading}/>;
      case 'Evaluasi Model':return <Evaluasi model={model} modelLoading={modelLoading} comparison={comparison} comparisonLoading={comparisonLoading}/>;
      case 'Laporan & Ringkasan':return <Laporan data={data} go={go}/>;
      case 'Kelola Data':return <KelolaData meta={meta} data={data} filters={filters} reload={reload}/>;
      default:return null;
    }
  }
  let content;
  if(authRequired)content=<Notice tone="warning"><form onSubmit={event=>{event.preventDefault();setToken(tokenInput.trim());setTokenInput('');setAuthRequired(false);reload()}}><strong>Masuk diperlukan.</strong> Tempel token akses dari pengelola. Token disimpan hanya pada tab ini.<label className="field"><span>Token akses</span><input type="password" autoComplete="off" aria-label="Token akses" value={tokenInput} onChange={event=>setTokenInput(event.target.value)}/></label><button className="button primary" type="submit" disabled={!tokenInput.trim()}>Masuk</button></form></Notice>;
  else if(meta?.access_restricted)content=<Notice tone="warning">{meta.message}</Notice>;
  else if(meta?.warehouse_empty)content=<Empty message={meta.message}/>;
  else if(independent && meta)content=current();
  else if(loading)content=<Loading/>;
  else if(data)content=current();
  else if(!error)content=<Empty message="Belum ada data yang dapat dibaca dari warehouse."/>;

  return <div className="app-shell">
    <Sidebar page={page} changePage={go} isOpen={menu} setOpen={setMenu}/>
    <main className="main-area" id="main-content">
      <Header page={page} meta={meta} setOpen={setMenu}/>
      <div className="source-banner"><b>{!meta?'MEMUAT SUMBER':meta.warehouse_empty?'BELUM ADA DATA':meta.source_kind==='synthetic'?'DATA SINTETIS / SIMULASI':'DATA TERBATAS'}</b><span>{meta?.message||'Menghubungkan dashboard ke warehouse.'}</span></div>
      <div className="data-actions"><button className="button light" type="button" onClick={reload} disabled={loading}>Muat ulang data</button><span>Membaca ulang PostgreSQL; pemuatan data dilakukan lewat ETL manual.</span></div>
      {meta&&!meta.warehouse_empty&&!meta.access_restricted&&!baselinePage&&<FilterBar meta={meta} filters={filters} setFilters={setFilters} loading={loading}/>}
      {baselinePage&&<Notice>Halaman baseline mempertahankan eksperimen ML yang tersedia. Metrik berasal dari artefak eksperimen; filter analitik tidak menghitung ulang model.</Notice>}
      {error&&<Notice tone="error">Gagal membaca data: {error} <button className="link-button" type="button" onClick={reload}>Coba baca ulang</button></Notice>}
      {modelError&&baselinePage&&<Notice tone="warning">Hasil eksperimen belum dapat dimuat: {modelError}. <button className="link-button" onClick={()=>setModelRevision(value=>value+1)}>Coba lagi</button></Notice>}
      {content}
      <Footer meta={meta}/>
    </main>
  </div>;
}
