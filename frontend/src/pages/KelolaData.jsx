import React,{useEffect,useState} from 'react';
import {Database,Download,FileCheck2} from 'lucide-react';
import {Card,Notice} from '../components/Common';
import {api,whole,queryString,download} from '../lib/api';

export default function KelolaData({meta,data,filters,reload}){
 const [error,setError]=useState(''),[busy,setBusy]=useState('');
 const [readiness,setReadiness]=useState(null),[readinessError,setReadinessError]=useState('');
 const q=data?.filtered_quality, batch=data?.quality;
 useEffect(()=>{
  let active=true;
  api('/data-readiness').then(result=>{if(active)setReadiness(result)}).catch(err=>{
   if(active)setReadinessError(err.message);
  });
  return ()=>{active=false};
 },[meta?.data_version,meta?.source_kind]);
 async function exportData(kind){
  setBusy(kind);setError('');
  try{await download('/api/data/export/'+kind+queryString(filters),'toba_'+kind+'.csv')}
  catch(err){setError(err.message)}finally{setBusy('')}
 }
 return <><Notice>Data dikelola melalui ETL manual setelah validasi dan persetujuan. Halaman ini hanya membaca PostgreSQL dan mengekspor hasil filter.</Notice>
 <div className="page-grid two"><Card title="Sumber aktif - seluruh warehouse" icon={Database}><div className="source-detail"><span>{meta?.source_kind==='synthetic'?'DATA SINTETIS / SIMULASI':meta?.access_restricted?'RINGKASAN AKTUAL TERBATAS':'BELUM ADA DATA'}</span><h3>{meta?.source}</h3>{meta?.access_restricted?<p>Jumlah responden dan catatan individual tidak ditampilkan pada tampilan terbatas.</p>:<><p>{whole(meta?.participants)} profil; {whole(meta?.daily_records)} catatan harian; {whole(meta?.session_records)} sesi tercatat</p><small>{meta?.min_date} - {meta?.max_date}</small></>}</div></Card>
 <Card title="Kualitas pada filter aktif" icon={FileCheck2}>{meta?.access_restricted?<Notice>Rincian filter dan baris individual disembunyikan untuk sumber aktual. Lihat ringkasan agregat readiness di bawah.</Notice>:q?<div className="quality-grid">{[['Catatan harian',q.daily_records],['Sesi tercatat',q.session_records],['Sesi tidak lengkap',q.incomplete_sessions],['Tidur kosong',q.missing_sleep_hours],['Duduk kosong',q.missing_sitting],['Jumlah merokok kosong',q.missing_smoke_count]].map(([label,value])=><div key={label}><span>{label}</span><b>{whole(value)}</b></div>)}</div>:<Notice>Kualitas pilihan belum dapat dibaca.</Notice>}</Card></div>
 {!meta?.access_restricted&&<Card title="Snapshot audit batch ETL CP2"><p>Versi audit: {meta?.etl_audit_version||'Laporan CP2 belum dimuat ke warehouse aktif'}.</p>{!meta?.etl_audit_version&&<Notice tone="warning">Perbaikan CP2 belum diterapkan pada data aktif. Pengelola perlu memeriksa dry-run dan menyetujui pemuatan melalui CLI.</Notice>}{batch&&<p>Snapshot saat impor: {whole(batch.accepted_profiles)} profil diterima; {whole(batch.accepted_daily)} harian diterima; {whole(batch.rejected_daily)} harian dikarantina. Angka snapshot ini berlaku untuk seluruh batch, bukan filter.</p>}</Card>}
 {!meta?.access_restricted&&batch?.pressure_anomalies&&<Notice>{whole(batch.pressure_anomalies.flagged_sessions)} sesi berflag IQR pada seluruh batch. Flag statistik bukan diagnosis atau bukti kesalahan; raw dipertahankan untuk review. Data aktual dengan isu belum terselesaikan diblokir quality gate.</Notice>}
 {!meta?.access_restricted&&<Card title="Unduh hasil filter" icon={Download}><div className="export-row">{[['participants','Profil'],['daily','Catatan harian'],['sessions','Sesi tensi']].map(([kind,label])=><button key={kind} type="button" className="button light" disabled={!!busy||!data} onClick={()=>exportData(kind)}><Download size={14}/>{busy===kind?'Mengunduh...':label}</button>)}</div>{error&&<Notice tone="error">{error}</Notice>}</Card>}
 <Card title="Kesiapan data dan analisis" icon={FileCheck2}>
 {readinessError&&<Notice tone="warning">Ringkasan readiness belum dapat dimuat: {readinessError}. Pastikan API terbaru berjalan dan akses pengelola tersedia.</Notice>}
 {readiness&&<><p><strong>{readiness.label}</strong> · Status teknis: {readiness.ml_status}</p>
 <div className="quality-grid">
 {[
 ['Responden / profil',readiness.profiles],['Tanggal pengamatan',readiness.date_count],
 ['Sesi valid',readiness.valid_sessions],['Sesi perlu review',readiness.unresolved_session_reviews],
 ['Baris profil karantina',readiness.profile_quarantined],['Baris harian karantina',readiness.daily_quarantined],
 ['Isu kualitas tercatat',readiness.issue_count],['Window histori 7 hari',readiness.history_7d_respondents],
 ['Window training 7+7 hari',readiness.training_windows_7d]
 ].map(([label,value])=><div key={label}><span>{label}</span><b>{whole(value)}</b></div>)}
 </div>
 <p>Periode tersedia: {readiness.min_date||'–'} sampai {readiness.max_date||'–'} ({whole(readiness.daily_records)} catatan harian; {whole(readiness.session_records)} sesi tercatat).</p>
 <Notice>{readiness.ml_note} Target yang diperiksa: <code>{readiness.training_target}</code>. Window dihitung hanya jika setiap hari memiliki sesi BP valid; hasil ini bukan persetujuan target atau validasi ilmiah.</Notice>
 </>}
 </Card>
 <Card title="Petunjuk validasi ETL"><p>Jalankan dari root project pada lingkungan Python yang benar. Perintah ini hanya validasi, tanpa mengubah database:</p><pre className="etl-command"><code>python -m etl.import_data --synthetic --dry-run --summary</code></pre><ol><li>Validasi dua formulir melalui ETL dry-run.</li><li>Periksa kualitas dan target database, lalu minta persetujuan pengelola.</li><li>Terapkan ETL manual dengan prasyarat hash target yang disetujui.</li><li>Klik Muat ulang data untuk membaca hasil terbaru.</li></ol><p>Dataset aktual memakai kontrak yang sama. Akses publik ke data aktual tetap dibatasi sampai kontrol akses tersedia.</p><button className="button light" type="button" onClick={reload}>Baca ulang warehouse</button></Card>
 </>;
}
