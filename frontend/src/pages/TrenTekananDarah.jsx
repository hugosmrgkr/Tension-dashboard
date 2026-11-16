import React,{useState} from 'react';
import {Card,Notice,MiniTable,Empty} from '../components/Common';
import {SessionPressureLines,SessionBox,SessionHeatmap} from '../components/Visuals';
import {fmt,whole} from '../lib/api';
import {ChartCard,Explainer} from '../components/page-shared/Analysis';

export default function Tren({data,onFilter,filters={}}){
 const [localId,setLocalId]=useState('');
 const rid=onFilter?(filters.respondent_id||''):localId;
 if(!data||!data.session_rows.length)return <Empty message={data?.message}/>;
 const ids=[...new Set(data.session_rows.map(row=>row.respondent_id))].sort();
 const rows=rid?data.session_rows.filter(row=>row.respondent_id===rid):data.session_rows,valid=rows.filter(row=>row.is_valid);
 const trend=rid&&!onFilter?aggregateTrend(valid):data.trend;
 return <><div className="table-toolbar"><label className="field"><span>Perinci riwayat satu responden</span><select aria-label="ID tren" value={rid} onChange={event=>onFilter?onFilter({respondent_id:event.target.value}):setLocalId(event.target.value)}><option value="">Semua pada filter</option>{ids.map(id=><option key={id} value={id}>{id}</option>)}</select></label><span>{whole(rows.length)} sesi tercatat; {whole(valid.length)} valid</span></div>
 <Notice>Dua pembacaan dirata-ratakan per sesi sesuai CP2. Satu pasangan lengkap pada nomor yang sama dapat dipakai bila tidak ada komponen ambigu. Sesi ambigu/tidak konsisten tetap pada tabel sebagai pending review dan tidak masuk grafik. Waktu pengamatan menggunakan tanggal formulir, bukan timestamp pengiriman.</Notice>
 {valid.length?<div className="page-grid two">
 {['Pagi','Malam'].map(session=><ChartCard key={session} title={`Tren Tekanan Darah ${session}`} sample={`${whole(valid.filter(row=>row.session===session).length)} sesi valid`} description={`SBP (sistolik) dan DBP (diastolik) sesi ${session.toLowerCase()} dibandingkan pada satu sumbu mmHg. Rerata per tanggal dari sesi valid pada filter yang sama dengan tabel detail. Klik titik untuk memilih tanggal-sesi; reset untuk kembali.`}><SessionPressureLines rows={trend} session={session} onSelect={onFilter}/></ChartCard>)}
 <ChartCard title="Distribusi SBP sesi" sample={`${whole(valid.length)} sesi valid`} description="Median dan kuartil merangkum penyebaran. Pencilan tetap dipertahankan untuk ditelusuri pada tabel."><SessionBox rows={valid}/></ChartCard>
 <ChartCard title="Heatmap SBP menurut waktu" sample={`${whole(valid.length)} sesi valid`} description="Warna = rerata SBP, tooltip = jumlah sesi. Klik sel untuk memilih tanggal dan Pagi/Malam; sel missing tidak diberi nol."><SessionHeatmap rows={trend} onSelect={onFilter}/></ChartCard>
 </div>:<Empty message={data.message}/>}
 <Card title="Detail pembacaan tekanan darah"><Explainer>Seluruh tekanan darah dalam mmHg. Dua pembacaan dan jumlah bacaan valid ditampilkan; satu baris = ID-tanggal-sesi. Missing ditampilkan sebagai tanda kosong.</Explainer><MiniTable rows={rows.map(row=>({...row,sbp_mean:fmt(row.sbp_mean,1),dbp_mean:fmt(row.dbp_mean,1),valid_label:row.is_valid?'Valid':row.review_status==='pending_review'?'Pending review':'Tidak lengkap'}))} columns={[["respondent_id","ID"],["date","Tanggal"],["session","Sesi"],["measured_at","Jam"],["sbp1","SBP 1"],["dbp1","DBP 1"],["sbp2","SBP 2"],["dbp2","DBP 2"],["sbp_mean","Rerata SBP"],["dbp_mean","Rerata DBP"],["valid_sbp_count","n SBP"],["valid_dbp_count","n DBP"],["valid_label","Status"]]}/></Card></>;
}
function aggregateTrend(rows){const map=new Map();for(const row of rows){const key=row.date+'|'+row.session,item=map.get(key)||{date:row.date,session:row.session,sbp:0,dbp:0,n:0};item.sbp+=row.sbp_mean;item.dbp+=row.dbp_mean;item.n++;map.set(key,item)}return [...map.values()].map(row=>({...row,sbp:row.sbp/row.n,dbp:row.dbp/row.n})).sort((a,b)=>a.date.localeCompare(b.date))}
