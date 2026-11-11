import React from 'react';
import {PlotlyChart,Empty} from './Common';
import {fmt} from '../lib/api';
const BLUE='#2789ed',ORANGE='#c58b36',TEAL='#397e8b';
const palette=[BLUE,TEAL,ORANGE,'#8664b1','#ca657f','#58a3bc'];
const sessions=['Pagi','Malam'];
const color={Pagi:BLUE,Malam:'#173b65'};
const point=event=>event?.points?.[0];

export function SessionPressureLines({rows=[],session,height=315,onSelect}){
 const selected=rows.filter(row=>row.session===session).sort((a,b)=>a.date.localeCompare(b.date));
 const traces=[['sbp','SBP',BLUE],['dbp','DBP','#173b65']].map(([field,label,lineColor])=>({
  type:'scatter',mode:'lines+markers',name:label,x:selected.map(row=>row.date),
  y:selected.map(row=>Number.isFinite(row[field])?row[field]:null),
  marker:{color:lineColor,size:6},line:{width:2.5,color:lineColor,dash:field==='dbp'?'dash':'solid'},connectgaps:false,
  customdata:selected.map(row=>[row.n,row.date,session]),
  hovertemplate:'%{x}<br>'+session+' · '+label+': %{y:.1f} mmHg<br>n=%{customdata[0]} sesi<extra></extra>'
 }));
 return <PlotlyChart height={height} data={traces}
  onClick={onSelect?event=>{const p=point(event);if(p?.customdata)onSelect({start_date:p.customdata[1],end_date:p.customdata[1],session:p.customdata[2]})}:undefined}
  layout={{xaxis:{title:'Tanggal pengamatan',type:'date'},yaxis:{title:'Rata-rata tekanan darah (mmHg)'},hovermode:'x unified'}}/>;
}

export function SessionLines({rows=[],field='sbp',height=315,onSelect}){
 const traces=sessions.map(session=>{
  const a=rows.filter(row=>row.session===session).sort((a,b)=>a.date.localeCompare(b.date));
  return {type:'scatter',mode:'lines+markers',name:session,x:a.map(r=>r.date),y:a.map(r=>r[field]),
   marker:{color:color[session],size:6},line:{width:2.5,color:color[session]},connectgaps:false,
   customdata:a.map(r=>[r.n,r.date,session]),hovertemplate:'%{x}<br>'+session+': %{y:.1f} mmHg<br>n=%{customdata[0]} sesi<extra></extra>'};
 });
 return <PlotlyChart height={height} data={traces} onClick={onSelect?event=>{const p=point(event);if(p?.customdata)onSelect({start_date:p.customdata[1],end_date:p.customdata[1],session:p.customdata[2]})}:undefined}
  layout={{xaxis:{title:'Tanggal pengamatan',type:'date'},yaxis:{title:`Rata-rata ${field.toUpperCase()} (mmHg)`},hovermode:'x unified'}}/>;
}
export function SessionBox({rows=[],field='sbp_mean',violin=false,group='session',height=310}){
 const groups=[...new Set(rows.map(r=>r[group]).filter(Boolean))].sort();
 return <PlotlyChart height={height} data={groups.map((name,i)=>{
  const a=rows.filter(r=>r[group]===name&&Number.isFinite(r[field]));
  return {type:violin?'violin':'box',name,y:a.map(r=>r[field]),box:violin?{visible:true}:undefined,
   boxpoints:violin?undefined:'outliers',meanline:{visible:violin},line:{color:group==='session'?(color[name]||BLUE):palette[i%palette.length]},
   customdata:a.map(()=>a.length),hovertemplate:name+'<br>%{y:.1f} mmHg<br>n=%{customdata} sesi<extra></extra>'};
 })} layout={{yaxis:{title:`${field.startsWith('dbp')?'DBP':'SBP'} (mmHg)`},xaxis:{title:group==='session'?'Sesi pengukuran':'Kelompok usia (tahun)'},showlegend:false}}/>;
}
export function SessionHeatmap({rows=[],onSelect}){
 const dates=[...new Set(rows.map(r=>r.date))].sort();
 const cells=sessions.map(session=>dates.map(date=>rows.find(r=>r.date===date&&r.session===session)));
 return <PlotlyChart height={310} data={[{type:'heatmap',x:dates,y:sessions,z:cells.map(a=>a.map(r=>r?.sbp??null)),
  customdata:cells.map(a=>a.map(r=>r?.n??null)),hoverongaps:false,colorscale:[[0,'#e5f0ff'],[.5,'#74adf5'],[1,'#163b7b']],
  hovertemplate:'%{x}<br>%{y}: %{z:.1f} mmHg<br>n=%{customdata} sesi<extra></extra>',colorbar:{title:'SBP<br>mmHg'}}]}
  onClick={onSelect?event=>{const p=point(event);if(p?.z!=null)onSelect({start_date:p.x,end_date:p.x,session:p.y})}:undefined}
  layout={{xaxis:{title:'Tanggal pengamatan',type:'date'},yaxis:{title:'Sesi pengukuran'}}}/>;
}
export function NumericScatter({rows=[],xkey,ykey='sbp_mean',xlabel,title='SBP',height=305,onSelect}){
 const a=rows.filter(r=>Number.isFinite(r[xkey])&&Number.isFinite(r[ykey]));
 return <PlotlyChart height={height} data={[{type:'scatter',mode:'markers',x:a.map(r=>r[xkey]),y:a.map(r=>r[ykey]),
  customdata:a.map(r=>[r.respondent_id,r.date]),marker:{color:BLUE,size:7,opacity:.6},
  hovertemplate:'%{customdata[0]} | %{customdata[1]}<br>'+xlabel+': %{x}<br>'+title+': %{y:.1f} mmHg<extra></extra>'}]}
  onClick={onSelect?event=>{const p=point(event);if(p?.customdata)onSelect({respondent_id:p.customdata[0],start_date:p.customdata[1],end_date:p.customdata[1]})}:undefined}
  layout={{xaxis:{title:xlabel},yaxis:{title:title+' (mmHg)'},showlegend:false}}/>;
}
export function StressBox({rows=[]}){
 return <PlotlyChart data={[1,2,3,4,5].map((level,i)=>({type:'box',name:String(level),y:rows.filter(r=>r.stress===level&&Number.isFinite(r.sbp_mean)).map(r=>r.sbp_mean),marker:{color:palette[i]}}))}
  layout={{xaxis:{title:'Tingkat stres (skala 1 sampai 5)'},yaxis:{title:'SBP harian (mmHg)'},showlegend:false}}/>;
}
export function CategoryBars({rows=[]}){
 return <PlotlyChart height={Math.max(310,rows.length*36+90)} data={[{type:'bar',orientation:'h',x:rows.map(r=>r.sbp),y:rows.map(r=>r.category),
  customdata:rows.map(r=>[r.n,r.respondents]),marker:{color:BLUE},
  hovertemplate:'%{y}<br>SBP %{x:.1f} mmHg<br>n=%{customdata[0]} hari, %{customdata[1]} ID<extra></extra>'}]}
  layout={{margin:{l:155,r:20,t:16,b:60},xaxis:{title:'Rata-rata SBP harian (mmHg)'},yaxis:{automargin:true,autorange:'reversed',title:'Kategori jawaban'},showlegend:false}}/>;
}
export function CountBars({rows=[],onSelect,unit='responden'}){
 return <PlotlyChart height={Math.max(280,rows.length*30+85)} data={[{type:'bar',orientation:'h',x:rows.map(r=>r.n),y:rows.map(r=>r.category),
  marker:{color:BLUE},hovertemplate:'%{y}<br>%{x} '+unit+'<extra></extra>'}]} onClick={onSelect?event=>{const p=point(event);if(p?.y&&p.y!=='Tidak diketahui')onSelect(p.y)}:undefined}
  layout={{margin:{l:150,r:16,t:14,b:55},xaxis:{title:`Jumlah ${unit}`,dtick:1},yaxis:{title:'Kategori',autorange:'reversed',automargin:true},showlegend:false}}/>;
}
export function Histogram({rows=[],field,label,unit}){
 const a=rows.filter(r=>Number.isFinite(r[field]));
 return <PlotlyChart data={[{type:'histogram',x:a.map(r=>r[field]),marker:{color:BLUE,line:{color:'white',width:1}},hovertemplate:label+': %{x}<br>%{y} responden<extra></extra>'}]}
  layout={{xaxis:{title:`${label} (${unit})`},yaxis:{title:'Jumlah responden',dtick:1},showlegend:false,bargap:.08}}/>;
}
export function PieCategories({rows=[],unit='catatan harian',onSelect}){
 return <PlotlyChart height={320} data={[{type:'pie',labels:rows.map(r=>r.category),values:rows.map(r=>r.n),hole:.56,textinfo:'percent',
  hovertemplate:'%{label}: %{value} '+unit+' (%{percent})<extra></extra>',marker:{colors:palette}}]}
  onClick={onSelect?event=>{const p=point(event);if(p?.label&&p.label!=='Tidak diketahui')onSelect(p.label)}:undefined}
  layout={{showlegend:true,legend:{orientation:'h',y:-.12},margin:{l:12,r:12,t:15,b:75}}}/>;
}
export function WorkTreemap({rows=[]}){
 return <PlotlyChart height={320} data={[{type:'treemap',labels:rows.map(r=>r.category),parents:rows.map(()=>''),values:rows.map(r=>r.n),textinfo:'label+value',
  marker:{colorscale:'Blues'},hovertemplate:'%{label}<br>%{value} catatan harian<extra></extra>'}]} layout={{margin:{l:0,r:0,t:12,b:8}}}/>;
}
export function SmallMultiples({rows=[]}){
 const groups=[...new Set(rows.map(r=>r.age_group))].filter(Boolean).sort();
 const values=rows.map(row=>row.sbp).filter(Number.isFinite);
 const range=values.length?[Math.min(...values)*.98,Math.max(...values)*1.02]:undefined;
 if(!groups.length)return <Empty message="Belum ada sesi valid untuk grafik kelompok usia."/>;
 return <div className="small-multiples">{groups.map(group=>{const a=rows.filter(r=>r.age_group===group).sort((a,b)=>a.date.localeCompare(b.date));return <div key={group}><b>Usia {group} tahun</b>
  <PlotlyChart height={220} data={[{type:'scatter',mode:'lines+markers',x:a.map(r=>r.date),y:a.map(r=>r.sbp),marker:{color:BLUE,size:4},customdata:a.map(r=>r.n),
   hovertemplate:'%{x}: %{y:.1f} mmHg<br>n=%{customdata} sesi<extra></extra>'}]} layout={{margin:{l:55,r:8,t:12,b:55},yaxis:{title:'SBP (mmHg)',range},xaxis:{title:'Tanggal',type:'date',tickformat:'%d %b'},showlegend:false}}/></div>})}</div>;
}
export function ModelComparison({model}){
 const scores=model?.scores||[];
 return <PlotlyChart height={300} data={[{type:'bar',x:scores.map(r=>r.model),y:scores.map(r=>r.mae),marker:{color:[ORANGE,BLUE]},text:scores.map(r=>fmt(r.mae,2)),textposition:'outside',hovertemplate:'%{x}<br>MAE %{y:.3f} mmHg<extra></extra>'}]}
  layout={{xaxis:{title:'Metode eksperimen'},yaxis:{title:'MAE (mmHg)',range:scores.length?[0,Math.max(...scores.map(row=>row.mae))*1.2||1]:undefined},showlegend:false}}/>;
}
const validPredictions=(model,field='linear')=>(model?.actual_vs_predicted||[]).filter(r=>Number.isFinite(r.actual)&&Number.isFinite(r[field]));
export function ActualVsPredicted({model,field='linear',label='Linear Regression'}){
 const a=validPredictions(model,field);if(!a.length)return <Empty message="Pasangan aktual-prediksi belum tersedia pada artefak eksperimen."/>;
 const values=a.flatMap(r=>[r.actual,r[field]]),bounds=[Math.min(...values),Math.max(...values)];
 return <PlotlyChart height={320} data={[{type:'scatter',mode:'markers',name:label,x:a.map(r=>r.actual),y:a.map(r=>r[field]),marker:{color:BLUE,opacity:.6},hovertemplate:'Aktual %{x:.1f} mmHg<br>Prediksi %{y:.1f} mmHg<extra></extra>'},
  {type:'scatter',mode:'lines',name:'Prediksi = aktual',x:bounds,y:bounds,line:{color:'#8194af',dash:'dash'}}]} layout={{xaxis:{title:'Aktual (mmHg)'},yaxis:{title:'Prediksi (mmHg)'}}}/>;
}
export function ResidualPlot({model,field='linear'}){
 const a=validPredictions(model,field);if(!a.length)return <Empty message="Residual belum tersedia pada artefak eksperimen."/>;
 const values=a.map(r=>r[field]);
 return <PlotlyChart height={320} data={[{type:'scatter',mode:'markers',name:'Residual',x:values,y:a.map(r=>r.actual-r[field]),marker:{color:TEAL,opacity:.65},hovertemplate:'Prediksi %{x:.1f} mmHg<br>Residual %{y:.1f} mmHg<extra></extra>'},
  {type:'scatter',mode:'lines',name:'Residual nol',x:[Math.min(...values),Math.max(...values)],y:[0,0],line:{dash:'dash',color:'#8194af'}}]}
  layout={{xaxis:{title:'Prediksi (mmHg)'},yaxis:{title:'Residual aktual - prediksi (mmHg)'},showlegend:false}}/>;
}

export function ValidationVsTest({comparison,metric='rmse'}){
 const rows=comparison?.comparison||[];if(!rows.length)return <Empty message="Hasil perbandingan belum tersedia."/>;
 const label=metric.toUpperCase();
 return <PlotlyChart height={320} data={[{type:'bar',name:'Validasi (leave-ID-out)',x:rows.map(r=>r.model),y:rows.map(r=>r.validation[metric]),marker:{color:BLUE},hovertemplate:'%{x}<br>Validasi '+label+' %{y:.3f} mmHg<extra></extra>'},
  {type:'bar',name:'Test utama',x:rows.map(r=>r.model),y:rows.map(r=>r.test[metric]),marker:{color:ORANGE},hovertemplate:'%{x}<br>Test '+label+' %{y:.3f} mmHg<extra></extra>'}]}
  layout={{barmode:'group',xaxis:{title:'Metode'},yaxis:{title:label+' (mmHg)',rangemode:'tozero'},legend:{orientation:'h'}}}/>;
}
export function ResidualHistogram({model,field}){
 const a=validPredictions(model,field);if(!a.length)return <Empty message="Distribusi error belum tersedia."/>;
 return <PlotlyChart height={300} data={[{type:'histogram',x:a.map(r=>r.actual-r[field]),nbinsx:10,marker:{color:TEAL},hovertemplate:'Residual %{x} mmHg<br>%{y} origin<extra></extra>'}]}
  layout={{xaxis:{title:'Residual aktual - prediksi (mmHg)'},yaxis:{title:'Jumlah origin uji'},showlegend:false}}/>;
}
