import React from 'react';
import {Card,Empty,PlotlyChart} from '../Common';
import {Explainer} from '../page-shared/Analysis';
import {dateID,fmt} from '../../lib/api';

// Defensive presentation only: dates after origin must never be drawn as history.
export function historyForChart(result){
 if(!Array.isArray(result?.history_daily)||!result.history_start||!result.last_date)return [];
 const rows=result.history_daily.filter(row=>typeof row.date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(row.date)&&row.date>=result.history_start&&row.date<=result.last_date);
 if(new Set(rows.map(row=>row.date)).size!==rows.length)return [];
 return [...rows].sort((a,b)=>a.date.localeCompare(b.date));
}

export default function PredictionCharts({result}){
 const rows=historyForChart(result);
 const range=dateID(result.forecast_start)+' sampai '+dateID(result.forecast_end);
 return <div className="page-grid two prediction-charts">
  <Card title="Riwayat SBP dan DBP yang digunakan" className="analysis-card prediction-history">
   <p className="sample-note">ID {result.respondent_id} · {rows.length} hari pengamatan · {dateID(result.history_start)} sampai {dateID(result.last_date)}</p>
   {rows.length?<PlotlyChart height={310} data={[
    ['sbp','SBP','#2789ed','solid'],['dbp','DBP','#173b65','dash']
   ].map(([field,label,color,dash])=>({type:'scatter',mode:'lines+markers',name:label,
    x:rows.map(row=>row.date),y:rows.map(row=>Number.isFinite(row[field])?row[field]:null),
    connectgaps:false,line:{color,dash,width:2.5},marker:{color,size:6},
    hovertemplate:'%{x}<br>'+label+' harian: %{y:.1f} mmHg<extra></extra>'}))}
    layout={{xaxis:{title:'Tanggal pengamatan',type:'date',tickformat:'%d %b'},yaxis:{title:'Tekanan darah (mmHg)'},hovermode:'x unified'}}/>
    :<Empty message="Riwayat valid belum tersedia pada respons ini. Tidak ada titik pengamatan yang dibuat otomatis."/>}
   <Explainer>Rerata sesi valid per hari untuk satu ID; Pagi/Malam digabung menjadi nilai harian sesuai fitur model. Missing DBP tidak diisi nol. Grafik berhenti pada origin, bukan pada akhir periode estimasi.</Explainer>
  </Card>
  <Card title="Estimasi rerata SBP tujuh hari berikutnya" className="analysis-card prediction-comparison">
   <p className="sample-note">Satu estimasi untuk rentang {range} · bukan tujuh prediksi harian</p>
   {Number.isFinite(result.prediction_mmHg)&&Number.isFinite(result.reference_naive_mmHg)?<PlotlyChart height={310}
    data={[{type:'bar',name:'Rerata SBP',x:['Model','Baseline naif'],
     y:[result.prediction_mmHg,result.reference_naive_mmHg],marker:{color:['#214f7d','#8ba4bf']},
     text:[fmt(result.prediction_mmHg,2),fmt(result.reference_naive_mmHg,2)],textposition:'auto',
     hovertemplate:'%{x}<br>Rerata SBP: %{y:.2f} mmHg<extra></extra>'}]}
    layout={{showlegend:false,xaxis:{title:'Metode estimasi'},yaxis:{title:'Rerata SBP (mmHg)',rangemode:'tozero'},bargap:.45}}/>
    :<Empty message="Estimasi valid belum tersedia; tidak ada angka pengganti."/>}
   <Explainer>Model menghasilkan satu rerata untuk seluruh rentang. Baseline naif memakai rerata SBP tujuh hari histori sebagai pembanding estimasi. Tidak ada prediksi DBP, nilai harian masa depan atau interval keyakinan yang dihitung.</Explainer>
  </Card>
 </div>;
}
