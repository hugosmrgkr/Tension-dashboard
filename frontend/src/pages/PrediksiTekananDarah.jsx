import React,{useEffect,useRef,useState} from 'react';
import {BookOpen,Target} from 'lucide-react';
import {Card,Notice,Loading} from '../components/Common';
import {api,fmt,dateID} from '../lib/api';
import {Explainer} from '../components/page-shared/Analysis';
import PredictionCharts from '../components/prediction/PredictionCharts';

export default function Prediksi({meta,model,modelLoading}){
 const [rid,setRid]=useState(''),[result,setResult]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 const [asof,setAsof]=useState('');
 const request=useRef(null),sequence=useRef(0);
 const ids=JSON.stringify(meta?.respondent_ids||[]);
 const context=JSON.stringify([meta?.source_kind,meta?.data_version,model?.run_id,model?.available,model?.error_code,model?.feature_schema_version]);
 useEffect(()=>{const choices=JSON.parse(ids);setRid(current=>choices.includes(current)?current:choices[0]||'');setAsof('');setResult(null);setError('');setLoading(false);sequence.current++;request.current?.abort()},[ids,context]);
 useEffect(()=>()=>{sequence.current++;request.current?.abort()},[]);
 function clear(){sequence.current++;request.current?.abort();setResult(null);setError('');setLoading(false)}
 function choose(value){clear();setRid(value);setAsof('')}
 async function submit(event){
  event.preventDefault();if(!rid)return;
  request.current?.abort();const controller=new AbortController(),serial=++sequence.current;request.current=controller;
  setError('');setLoading(true);setResult(null);
  try{
   const response=await api('/model/predict?respondent_id='+encodeURIComponent(rid)+(asof?'&asof_date='+encodeURIComponent(asof):''),{signal:controller.signal});
   if(serial!==sequence.current)return;
   if(response.respondent_id!==rid||(asof&&response.last_date!==asof)||
      (model?.run_id&&response.model?.version!==model.run_id)||
      (meta?.data_version&&response.data_version&&meta.data_version!==response.data_version))throw new Error('Konteks ID, data atau model berubah. Muat ulang data sebelum mencoba lagi');
   if(!Number.isFinite(response.prediction_mmHg)||!Number.isFinite(response.reference_naive_mmHg))throw new Error('Respons prediksi tidak berisi nilai yang valid');
   setResult(response);
  }
  catch(err){if(serial===sequence.current&&err.name!=='AbortError')setError(err.message)}
  finally{if(serial===sequence.current)setLoading(false)}
 }
 const m=result?.model;
 return <><Notice tone="warning"><strong>Model eksperimen - DATA SINTETIS / SIMULASI.</strong> Memperkirakan rerata sistolik tujuh hari berikutnya (mmHg), bukan klasifikasi hipertensi atau diagnosis. Target belum disetujui dosen (target_approved=false).</Notice>
 {modelLoading&&<Loading/>}
 {!modelLoading&&!model?.available&&<Notice tone="warning">{model?.message||'Artefak model belum tersedia. Tidak ada perkiraan contoh yang diisi otomatis.'}</Notice>}
 <div className="page-grid two"><Card title="Input: riwayat responden simulasi" icon={Target}><form className="predict-form" onSubmit={submit}><label className="field"><span>ID responden simulasi</span><select aria-label="ID prediksi model" value={rid} onChange={event=>choose(event.target.value)}>{(meta?.respondent_ids||[]).map(id=><option key={id} value={id}>{id}</option>)}</select></label>
 <label className="field"><span>Origin pengamatan (opsional)</span><input type="date" aria-label="Tanggal origin prediksi" min={meta?.min_date} max={meta?.max_date} value={asof} onChange={event=>{clear();setAsof(event.target.value)}}/></label>
 <small className="muted">Kosongkan untuk memakai tanggal terakhir dengan SBP tersedia pada ID ini. Prediksi memakai histori sampai akhir origin; tidak mengikuti filter kelompok pada halaman analitik.</small>
 <p className="muted">Model memerlukan tujuh hari kalender berturut-turut pada akhir riwayat ID. Anda memilih riwayat yang sudah ada di PostgreSQL; fitur dihitung server dengan rumus yang sama seperti saat training.</p>
 <button className="button primary" type="submit" disabled={loading||modelLoading||!rid||!model?.available}>{loading?'Menghitung...':'Hitung perkiraan model'}</button></form>
 {error&&<Notice tone="error">{error}. Periksa kelengkapan riwayat ID, lalu coba lagi.</Notice>}
 <div aria-live="polite">{result&&<div className="prediction-result"><span>Output: estimasi rerata SBP tujuh hari berikutnya</span><strong className="prediction-number">{fmt(result.prediction_mmHg,2)} mmHg</strong><small>ID {result.respondent_id} | Akhir riwayat {result.last_date}</small>{result.forecast_start&&<small>Rentang estimasi {result.forecast_start} sampai {result.forecast_end}</small>}<small>Pembanding baseline naif (rerata 7 hari terakhir): {fmt(result.reference_naive_mmHg,2)} mmHg</small><p>Model: {m?.algorithm} (versi {m?.version}). Tidak disertai interval keyakinan dan tidak digunakan untuk keputusan medis.</p>{(result.notes||[]).map(note=><Notice key={note} tone="warning">{note}</Notice>)}</div>}</div></Card>
 <Card title="Cara membaca prediksi" icon={BookOpen}><div className="guide-steps"><div><b>1</b><span>Pilih ID dengan sedikitnya tujuh hari berurutan. Riwayat terakhir ditentukan oleh tanggal data, bukan tanggal komputer.</span></div><div><b>2</b><span>Server memakai gate pasangan BP yang sama dengan analitik, menghitung fitur histori, lalu menjalankan model terlatih terverifikasi hash.</span></div><div><b>3</b><span>Bandingkan dengan angka baseline naif. Bila model tidak lebih baik dari naif pada validasi, peringatan ditampilkan di atas.</span></div></div>
 {m&&<dl className="model-meta"><dt>Algoritma</dt><dd>{m.algorithm}</dd><dt>Versi model</dt><dd>{m.version}</dd><dt>Target / horizon</dt><dd>{m.target} / {m.horizon_days} hari</dd><dt>Sumber eksperimen</dt><dd>{m.data_source}</dd><dt>Tanggal artefak</dt><dd>{m.trained_on} (metadata P2; bukan timestamp training terverifikasi)</dd><dt>Batch inferensi</dt><dd>{result.data_version||'Belum tercatat'}</dd><dt>Batch training</dt><dd>{result.training_data_version||'Belum tercatat'}</dd><dt>Kompatibilitas</dt><dd>{result.compatibility_status==='matched'?'Batch cocok':result.compatibility_status==='batch_unverified'?'Batch belum terverifikasi':'Status belum tersedia'}</dd><dt>Status target</dt><dd>{m.target_approved?'Disetujui':'Belum disetujui dosen'}</dd></dl>}
 <Explainer>Eksperimen pada data sintetis; tidak membuktikan performa pada responden asli. Aturan ilmiah final menunggu dosen.</Explainer></Card></div>
 {result&&<><p className="interaction-hint">Riwayat berakhir {dateID(result.last_date)}. Estimasi merangkum {dateID(result.forecast_start)} sampai {dateID(result.forecast_end)}. Grafik tidak menggambarkan pengamatan masa depan.</p><PredictionCharts result={result}/></>}
 </>;
}
