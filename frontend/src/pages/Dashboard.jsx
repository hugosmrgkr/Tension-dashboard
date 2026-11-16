import React from 'react';
import {Activity,ArrowRight,HeartPulse,UsersRound,CalendarDays} from 'lucide-react';
import {Card,Notice,Empty} from '../components/Common';
import {SessionPressureLines,SessionBox,SessionHeatmap} from '../components/Visuals';
import {fmt,whole} from '../lib/api';
import {ChartCard,Explainer} from '../components/page-shared/Analysis';

function KPI({icon:Icon,label,value,unit,desc,previous,current,def,count}){
 const delta=previous!=null&&Number.isFinite(current)?current-previous:null;
 return <div className="kpi kpi-biru"><div className="kpi-ico"><Icon size={22}/></div><div className="kpi-content"><div className="kpi-label" title={def?def.formula:desc}>{label}</div><div className="kpi-value">{value}<small>{unit}</small></div><div className="kpi-sub">{desc}</div>{def&&<details className="kpi-def"><summary>Definisi</summary><dl><dt>Rumus</dt><dd>{def.formula}</dd><dt>Satuan / grain</dt><dd>{def.unit} / {def.grain}</dd><dt>Filter</dt><dd>{def.filters}</dd>{count!=null&&<><dt>Data dipakai</dt><dd>{whole(count)} {def.unit}</dd></>}</dl></details>}{previous!=null&&<span className="kpi-compare">Sebelumnya {fmt(previous,unit?1:0)}{unit} | {delta>0?'+':''}{fmt(delta,unit?1:0)}{unit}</span>}</div></div>;
}
export function QualitySummary({data}){
 const q=data?.filtered_quality;if(!q)return <Notice>Kualitas pilihan belum dapat dibaca.</Notice>;
 const completeness=q.session_records?100*q.valid_sessions/q.session_records:null;
 return <Card title="Kualitas data pada filter aktif"><div className="quality-grid">{[
  ['Kelengkapan sesi',completeness==null?null:fmt(completeness,1)+'%'],['Sesi tidak lengkap/review',whole(q.incomplete_sessions)],['Sesi pending review',whole(q.pending_review_sessions)],['Tidur kosong',whole(q.missing_sleep_hours)],['Duduk kosong',whole(q.missing_sitting)],['Jumlah merokok kosong',whole(q.missing_smoke_count)]
 ].map(([label,value])=><div key={label}><span>{label}</span><b>{value??'Tidak tersedia'}</b></div>)}</div><Explainer>Kelengkapan sesi = sesi lolos gate pasangan pembacaan / seluruh sesi tercatat. Pasangan ambigu atau tidak konsisten menunggu review, bukan diagnosis. Missing perilaku dihitung per ID-tanggal, tidak diisi nol. Baris harian valid berarti diterima ETL, bukan semua kolom lengkap.</Explainer></Card>;
}
export default function Dashboard({data,go,onFilter}){
 if(!data||data.empty)return <Empty message={data?.message}/>;
 const k=data.kpis,prev=data.comparison?.has_data?data.comparison:null;
 return <>

 <div className="kpi-grid"><KPI icon={UsersRound} label="Responden aktif" def={data.kpi_definitions?.respondents} count={k.respondents} value={whole(k.respondents)} current={k.respondents} previous={prev?.active} desc="ID unik dengan catatan harian diterima ETL"/><KPI icon={CalendarDays} label="Catatan harian valid" def={data.kpi_definitions?.daily_records} count={k.daily_records} value={whole(k.daily_records)} current={k.daily_records} previous={prev?.daily} desc="ID-tanggal diterima ETL; missing tetap dipertahankan"/><KPI icon={Activity} label="Sesi valid" def={data.kpi_definitions?.sessions} count={k.sessions} value={whole(k.sessions)} current={k.sessions} previous={prev?.sessions} desc="Pasangan BP nomor sama; pending review dikecualikan"/><KPI icon={HeartPulse} label="Rata-rata SBP" def={data.kpi_definitions?.mean_sbp} count={k.sessions} value={fmt(k.mean_sbp,1)} current={k.mean_sbp} previous={prev?.sbp} unit=" mmHg" desc={`Rerata ${whole(k.sessions)} sesi valid, bukan rerata per orang`}/></div>
 <details className="period-context"><summary>Perbandingan periode</summary><Notice>{data.comparison_definition&&<small className="comparison-def">{data.comparison_definition} </small>}{data.comparison?data.comparison.has_data?`Pembanding: ${data.comparison.period}, periode sebelumnya dengan panjang yang sama dan filter non-tanggal yang sama. Selisih ditampilkan sebagai perubahan deskriptif, bukan indikator baik/buruk.`:`Belum ada data pembanding pada periode ${data.comparison.period}.`:'Pilih tanggal mulai dan sampai untuk membandingkan dengan periode sebelumnya yang sama panjang.'}</Notice></details>
 {data.message&&<Notice tone="warning">{data.message}</Notice>}
 <div className="dashboard-tools"><p className="interaction-hint">Klik titik tren atau sel heatmap untuk memperinci tanggal dan sesi.</p><button className="link-button" onClick={()=>go('Tren Tekanan Darah')}>Lihat detail tren <ArrowRight size={14}/></button></div>
 <div className="page-grid two">
 {['Pagi','Malam'].map(session=><ChartCard key={session} title={`Tren Tekanan Darah ${session}`} sample={`${whole(data.trend.filter(row=>row.session===session).reduce((sum,row)=>sum+row.n,0))} sesi valid`} description={`Perbandingan SBP (sistolik) dan DBP (diastolik) dalam mmHg pada sesi ${session.toLowerCase()}. Rerata per tanggal; tooltip menunjukkan jumlah sesi. Perubahan komposisi responden dapat memengaruhi pola, bukan diagnosis.`}><SessionPressureLines rows={data.trend} session={session} onSelect={onFilter}/></ChartCard>)}
 <ChartCard title="Distribusi SBP menurut sesi" sample={`${whole(k.sessions)} sesi valid`} description="Garis tengah kotak menunjukkan median; kotak menunjukkan kuartil. Titik ekstrem dipertahankan dan bukan diagnosis."><SessionBox rows={data.session_box}/></ChartCard>
 <ChartCard title="Heatmap SBP per tanggal dan sesi" sample={`${whole(k.dates)} tanggal dengan catatan harian`} description="Warna lebih pekat menunjukkan rerata SBP lebih tinggi, bukan tingkat diagnosis. Sel kosong berarti nilai tidak tersedia."><SessionHeatmap rows={data.heatmap} onSelect={onFilter}/></ChartCard>
 </div><QualitySummary data={data}/></>;
}
