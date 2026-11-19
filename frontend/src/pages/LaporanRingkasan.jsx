import React from 'react';
import {ArrowRight} from 'lucide-react';
import {Notice,Empty} from '../components/Common';
import {SessionLines} from '../components/Visuals';
import {fmt,whole} from '../lib/api';
import {ChartCard} from '../components/page-shared/Analysis';
import QualityOverview from '../components/research-summary/QualityOverview';

export default function Laporan({data,go}){
 if(!data||data.empty||data.kpis.sessions===0)return <Empty message={data?.message}/>;
 const k=data.kpis,q=data.filtered_quality;
 const pagi=data.session_stats.find(row=>row.session==='Pagi'),malam=data.session_stats.find(row=>row.session==='Malam');
 const first=data.trend.map(row=>row.date).sort()[0],last=data.trend.map(row=>row.date).sort().at(-1);
 const gap=pagi&&malam?malam.sbp-pagi.sbp:null;
 const findings=[
  [`${whole(k.respondents)} ID menyumbang ${whole(k.daily_records)} catatan harian`,`Cakupan ${first} sampai ${last}: ${whole(k.sessions)} sesi valid. Jumlah catatan berulang bukan jumlah individu independen.`],
  [`Rerata sesi ${fmt(k.mean_sbp,1)}/${fmt(k.mean_dbp,1)} mmHg`,`Rerata dihitung dari seluruh sesi valid, sehingga responden dengan lebih banyak sesi memiliki bobot pengamatan lebih besar. Ini bukan prevalensi atau diagnosis.`],
  [gap==null?'Perbandingan pagi-malam belum lengkap':`Selisih rerata Malam - Pagi ${gap>0?'+':''}${fmt(gap,2)} mmHg`,`Pagi n=${whole(pagi?.n)} sesi, Malam n=${whole(malam?.n)} sesi. Perbandingan ini tidak berpasangan per orang-hari dan tidak mengisolasi pengaruh waktu.`],
  [
  `${whole(q.valid_sessions)} dari ${whole(q.session_records)} sesi masuk perhitungan valid`,
  `${whole(q.incomplete_sessions)} sesi belum masuk perhitungan valid. Terdapat ${whole(q.pending_review_sessions)} sesi pending review. Pada catatan harian, ${whole(q.missing_sleep_hours)} nilai tidur, ${whole(q.missing_sitting)} nilai duduk, dan ${whole(q.missing_smoke_count)} jumlah merokok kosong.`],
  ['Keputusan kerja: periksa kelengkapan sebelum memperluas analisis','Telusuri periode, ID dan kategori dengan sampel kecil melalui filter. Dataset sintetis menguji alur teknis; temuan ini tidak menjadi rekomendasi kesehatan atau bukti penelitian aktual.']
 ];
 return <><div className="welcome"><div><span className="eyebrow">CERITA DATA PADA FILTER AKTIF</span><h2>Apa yang dapat disimpulkan, dan apa batasnya?</h2><p>Ringkasan diperbarui dari sumber yang sama dengan KPI dan grafik.</p></div></div>
 <div className="story-list">{findings.map(([title,description],index)=><article className="story" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{description}</p></div></article>)}</div>
 <QualityOverview quality={q}/>
 <ChartCard title={`SBP pada ${whole(k.sessions)} sesi valid selama ${whole(k.dates)} tanggal`} sample={`${whole(k.respondents)} ID aktif; ${first} sampai ${last}`} description="Garis menggambarkan rerata per tanggal-sesi. Perubahan komposisi responden dan missing dapat menjelaskan perubahan pola; data sintetis tidak mendukung inferensi populasi."><SessionLines rows={data.trend}/></ChartCard>
 <div className="data-actions"><button className="button primary" onClick={()=>go('Analisis Faktor Risiko')}>Periksa faktor gaya hidup <ArrowRight size={15}/></button><button className="button light" onClick={()=>go('Kelola Data')}>Periksa kualitas dan ekspor</button></div>
 <Notice>Keterbatasan: pengukuran berulang, ukuran kelompok tidak seimbang, data laporan mandiri, potensi faktor perancu, serta definisi tidur aktual dan target ML yang belum final. Hasil masih DATA SINTETIS / SIMULASI.</Notice></>;
}
