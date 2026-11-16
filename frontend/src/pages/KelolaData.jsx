import React,{useState} from 'react';
import {Database,Download,FileCheck2} from 'lucide-react';
import {Card,Notice} from '../components/Common';
import {api,whole,queryString,download} from '../lib/api';

export default function KelolaData({meta,data,filters,reload}){
 const [error,setError]=useState(''),[busy,setBusy]=useState('');
 const q=data?.filtered_quality, batch=data?.quality;
 async function exportData(kind){
  setBusy(kind);setError('');
  try{await download('/api/data/export/'+kind+queryString(filters),'toba_'+kind+'.csv')}
  catch(err){setError(err.message)}finally{setBusy('')}
 }
 return <><Notice>Data dikelola melalui ETL manual setelah validasi dan persetujuan. Halaman ini hanya membaca PostgreSQL dan mengekspor hasil filter.</Notice>
 <div className="page-grid two"><Card title="Sumber aktif - seluruh warehouse" icon={Database}><div className="source-detail"><span>{meta?.source_kind==='synthetic'?'DATA SINTETIS / SIMULASI':'DATA TERBATAS'}</span><h3>{meta?.source}</h3><p>{whole(meta?.participants)} profil; {whole(meta?.daily_records)} catatan harian; {whole(meta?.session_records)} sesi tercatat</p><small>{meta?.min_date} - {meta?.max_date}</small></div></Card>
 <Card title="Kualitas pada filter aktif" icon={FileCheck2}>{q?<div className="quality-grid">{[['Catatan harian',q.daily_records],['Sesi tercatat',q.session_records],['Sesi tidak lengkap',q.incomplete_sessions],['Tidur kosong',q.missing_sleep_hours],['Duduk kosong',q.missing_sitting],['Jumlah merokok kosong',q.missing_smoke_count]].map(([label,value])=><div key={label}><span>{label}</span><b>{whole(value)}</b></div>)}</div>:<Notice>Kualitas pilihan belum dapat dibaca.</Notice>}</Card></div>
 <Card title="Snapshot audit batch ETL CP2"><p>Versi audit: {meta?.etl_audit_version||'Laporan CP2 belum dimuat ke warehouse aktif'}.</p>{!meta?.etl_audit_version&&<Notice tone="warning">Perbaikan CP2 belum diterapkan pada data aktif. Pengelola perlu memeriksa dry-run dan menyetujui pemuatan melalui CLI.</Notice>}{batch&&<p>Snapshot saat impor: {whole(batch.accepted_profiles)} profil diterima; {whole(batch.accepted_daily)} harian diterima; {whole(batch.rejected_daily)} harian dikarantina. Angka snapshot ini berlaku untuk seluruh batch, bukan filter.</p>}</Card>
 {batch?.pressure_anomalies&&<Notice>{whole(batch.pressure_anomalies.flagged_sessions)} sesi berflag IQR pada seluruh batch. Flag statistik bukan diagnosis atau bukti kesalahan; raw dipertahankan untuk review. Data aktual dengan isu belum terselesaikan diblokir quality gate.</Notice>}
 <Card title="Unduh hasil filter" icon={Download}><div className="export-row">{[['participants','Profil'],['daily','Catatan harian'],['sessions','Sesi tensi']].map(([kind,label])=><button key={kind} type="button" className="button light" disabled={!!busy||!data} onClick={()=>exportData(kind)}><Download size={14}/>{busy===kind?'Mengunduh...':label}</button>)}</div>{error&&<Notice tone="error">{error}</Notice>}</Card>
 <Card title="Petunjuk validasi ETL"><p>Jalankan dari root project pada lingkungan Python yang benar. Perintah ini hanya validasi, tanpa mengubah database:</p><pre className="etl-command"><code>python -m etl.import_data --synthetic --dry-run --summary</code></pre><ol><li>Validasi dua formulir melalui ETL dry-run.</li><li>Periksa kualitas dan target database, lalu minta persetujuan pengelola.</li><li>Terapkan ETL manual dengan prasyarat hash target yang disetujui.</li><li>Klik Muat ulang data untuk membaca hasil terbaru.</li></ol><p>Dataset aktual memakai kontrak yang sama. Akses publik ke data aktual tetap dibatasi sampai kontrol akses tersedia.</p><button className="button light" type="button" onClick={reload}>Baca ulang warehouse</button></Card>
 </>;
}
