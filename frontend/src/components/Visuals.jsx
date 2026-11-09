import React from 'react';
import {PlotlyChart} from './Common';
import {fmt} from '../lib/api';
const BLUE='#2f6fe0',NAVY='#0f2a5e',ORANGE='#f3a546',TEAL='#20a99c';
const sessColors={Pagi:BLUE,Malam:ORANGE};
const lineStyle=(label,field,arr)=>(arr||[]).filter(x=>x.session===label).map(x=>({x:x.date,y:x[field],n:x.n}));
export function SessionLines({rows,field='sbp',height=315}){
 return <PlotlyChart height={height} data={['Pagi','Malam'].map(s=>{const data=lineStyle(s,field,rows);return {type:'scatter',mode:'lines+markers',name:s,x:data.map(x=>x.x),y:data.map(x=>x.y),marker:{color:sessColors[s],size:5},line:{width:2.5,color:sessColors[s]},customdata:data.map(x=>x.n),hovertemplate:'%{x}<br>'+s+': %{y:.1f} mmHg<br>n=%{customdata} sesi<extra></extra>'}})} layout={{xaxis:{title:'Tanggal pengamatan',type:'date'},yaxis:{title:`Rata-rata ${field.toUpperCase()} (mmHg)`},hovermode:'x unified',margin:{l:58,r:14,t:25,b:60}}}/>;
}
export function SessionBox({rows,field='sbp_mean',violin=false,group='session',height=310}){
 const groups=[...new Set((rows||[]).map(x=>x[group]).filter(Boolean))].sort();
 return <PlotlyChart height={height} data={groups.map((k,i)=>({type:violin?'violin':'box',name:k,y:rows.filter(x=>x[group]===k&&x[field]!=null).map(x=>x[field]),boxpoints:violin?false:'outliers',meanline:{visible:violin},line:{color:[BLUE,ORANGE,TEAL,'#9980d4'][i%4]},fillcolor:['#dce9ff','#ffe9cf','#cff4eb','#eae3fa'][i%4],marker:{color:[BLUE,ORANGE,TEAL,'#9980d4'][i%4]}}))} layout={{yaxis:{title:`Tekanan darah (mmHg)`},xaxis:{title:group==='session'?'Sesi':'Kelompok'},showlegend:false}}/>;
}
export function SessionHeatmap({rows}){
 const dates=[...new Set(rows.map(x=>x.date))].sort();const ys=['Pagi','Malam'];
 const z=ys.map(s=>dates.map(d=>rows.find(x=>x.date===d&&x.session===s)?.sbp??null));
 return <PlotlyChart height={295} data={[{type:'heatmap',x:dates,y:ys,z,colorscale:[[0,'#e5f0ff'],[.5,'#74adf5'],[1,'#163b7b']],hovertemplate:'Tanggal %{x}<br>%{y}: %{z:.1f} mmHg<extra></extra>',colorbar:{title:'mmHg'}}]} layout={{xaxis:{title:'Tanggal'},margin:{l:60,r:10,t:20,b:65}}}/>;
}
export function NumericScatter({rows,xkey,ykey='sbp_mean',xlabel,title='Sistolik',height=305}){
 const valid=(rows||[]).filter(x=>typeof x[xkey]==='number'&&typeof x[ykey]==='number');
 return <PlotlyChart height={height} data={[{type:'scatter',mode:'markers',x:valid.map(x=>x[xkey]),y:valid.map(x=>x[ykey]),customdata:valid.map(x=>x.respondent_id+' · '+x.date),marker:{color:BLUE,size:7,opacity:.56},hovertemplate:'%{customdata}<br>'+xlabel+': %{x}<br>'+title+': %{y:.1f} mmHg<extra></extra>'}]} layout={{xaxis:{title:xlabel},yaxis:{title:title+' (mmHg)'},showlegend:false}}/>;
}
export function StressBox({rows}){
 return <PlotlyChart data={[1,2,3,4,5].map((value,i)=>({type:'box',name:String(value),y:rows.filter(x=>x.stress===value&&x.sbp_mean!=null).map(x=>x.sbp_mean),marker:{color:[TEAL,BLUE,'#7d9ff1',ORANGE,'#d9697d'][i]}}))} layout={{xaxis:{title:'Tingkat stres (1–5)'},yaxis:{title:'SBP harian (mmHg)'},showlegend:false}}/>;
}
export function CategoryBars({rows,label='Kategori',height=320}){
 const a=(rows||[]).slice(0,12);return <PlotlyChart height={height} data={[{type:'bar',orientation:'h',x:a.map(x=>x.sbp),y:a.map(x=>x.category),customdata:a.map(x=>x.n),marker:{color:BLUE},hovertemplate:'%{y}<br>Rata-rata: %{x:.1f} mmHg<br>n=%{customdata} hari<extra></extra>'}]} layout={{margin:{l:185,r:25,t:20,b:50},xaxis:{title:'Rata-rata SBP harian (mmHg)'},yaxis:{automargin:true,autorange:'reversed'},showlegend:false}}/>;
}
export function PieCategories({rows}){
 return <PlotlyChart height={300} data={[{type:'pie',labels:(rows||[]).map(x=>x.category),values:(rows||[]).map(x=>x.n),hole:.53,textinfo:'percent',hovertemplate:'%{label}: %{value} catatan<extra></extra>',marker:{colors:['#2f6fe0','#20a99c','#f3a546','#9980d4','#ee7580','#78bde9']}}]} layout={{showlegend:true,legend:{orientation:'h',y:-.1}}}/>;
}
export function WorkTreemap({rows}){
 return <PlotlyChart height={320} data={[{type:'treemap',labels:(rows||[]).map(x=>x.category),parents:(rows||[]).map(()=>''),values:(rows||[]).map(x=>x.n),textinfo:'label+value',marker:{colorscale:'Blues',showscale:false},hovertemplate:'%{label}: %{value} hari<extra></extra>'}]} layout={{margin:{l:2,r:2,t:5,b:5}}}/>;
}
export function SmallMultiples({rows}){
 const groups=[...new Set(rows.map(x=>x.age_group))].filter(Boolean).sort();
 return <div className="small-multiples">{groups.map(g=>{const a=rows.filter(x=>x.age_group===g);return <div key={g}><b>{g} tahun</b><PlotlyChart height={200} data={[{type:'scatter',mode:'lines',x:a.map(x=>x.date),y:a.map(x=>x.sbp),line:{color:BLUE,width:2},customdata:a.map(x=>x.n),hovertemplate:'%{x}: %{y:.1f} mmHg · n=%{customdata}<extra></extra>'}]} layout={{margin:{l:40,r:8,t:10,b:30},yaxis:{title:'SBP'},xaxis:{type:'date',tickformat:'%d %b'},showlegend:false}}/></div>})}</div>;
}
export function ModelComparison({model}){
 const scores=model?.scores||[];
 return <PlotlyChart height={270} data={[{type:'bar',x:scores.map(x=>x.model),y:scores.map(x=>x.mae),marker:{color:[ORANGE,BLUE]},text:scores.map(x=>fmt(x.mae,2)),textposition:'outside',hovertemplate:'%{x}<br>MAE %{y:.3f} mmHg<extra></extra>'}]} layout={{yaxis:{title:'MAE (mmHg), lebih kecil lebih baik',rangemode:'tozero'},showlegend:false}}/>;
}
export function ActualVsPredicted({model}){
 const a=model?.actual_vs_predicted||[];
 return <PlotlyChart height={320} data={[{type:'scatter',mode:'markers',name:'Linear Regression',x:a.map(x=>x.actual),y:a.map(x=>x.linear),marker:{color:BLUE,opacity:.6},hovertemplate:'Aktual %{x:.1f}<br>Prediksi %{y:.1f}<extra></extra>'},{type:'scatter',mode:'lines',name:'Ideal',x:[85,180],y:[85,180],line:{color:'#98a9c7',dash:'dash'}}]} layout={{xaxis:{title:'Aktual (mmHg)'},yaxis:{title:'Prediksi (mmHg)'},showlegend:true}}/>;
}
export function ResidualPlot({model}){
 const a=model?.actual_vs_predicted||[];
 return <PlotlyChart height={320} data={[{type:'scatter',mode:'markers',x:a.map(x=>x.linear),y:a.map(x=>x.actual-x.linear),marker:{color:TEAL,opacity:.62},hovertemplate:'Prediksi %{x:.1f}<br>Residual %{y:.1f}<extra></extra>'},{type:'scatter',mode:'lines',x:[80,180],y:[0,0],line:{dash:'dash',color:'#98a9c7'}}]} layout={{xaxis:{title:'Prediksi (mmHg)'},yaxis:{title:'Residual (aktual - prediksi), mmHg'},showlegend:false}}/>;
}
