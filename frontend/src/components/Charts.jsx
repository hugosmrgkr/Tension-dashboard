import React from 'react';
import { PlotlyChart, Card } from './Common';
import { LABELS, COLORS, fmt } from '../lib/api';

const BIRU='#2f6fe0', ORANYE='#f59e0b', NAVY='#15264b';
export const legendTop={orientation:'h',x:0,y:1.18,font:{size:10}};
const line=(x,y,name,color)=>({x,y,name,type:'scatter',mode:'lines+markers',line:{color,width:2.2},marker:{size:5},hovertemplate:'%{x}: %{y:.1f} mmHg<extra>'+name+'</extra>'});

export function LineTrends({trends, participant, setParticipant, participants}) {
 const source = participant && participant!=='Semua Partisipan' ? [] : trends;
 // For individual selection, caller supplies participantDaily instead of the aggregate.
 const t=source;
 return <><div className="chart-controls"><label>Partisipan&nbsp; <select value={participant} onChange={e=>setParticipant(e.target.value)}><option>Semua Partisipan</option>{participants?.map(p=><option key={p}>{p}</option>)}</select></label></div>
 <PlotlyChart height={220} data={[line(t.map(x=>x.tanggal),t.map(x=>x.sistolik_mean),'Sistolik',BIRU),line(t.map(x=>x.tanggal),t.map(x=>x.diastolik_mean),'Diastolik',ORANYE)]} layout={{legend:legendTop,margin:{l:45,r:8,t:30,b:33},yaxis:{title:{text:'Tekanan Darah (mmHg)',font:{size:10}},gridcolor:'#edf1f7'},xaxis:{type:'date',tickformat:'%d %b',dtick:432000000,tickfont:{size:10}}}} />
 </>;
}

export function TrendPlot({trends, height=225}) {
 const dates=trends.map(x=>x.tanggal);
 return <PlotlyChart height={height} data={[line(dates,trends.map(x=>x.sistolik_mean),'Sistolik',BIRU),line(dates,trends.map(x=>x.diastolik_mean),'Diastolik',ORANYE)]} layout={{legend:legendTop,margin:{l:44,r:8,t:31,b:30},yaxis:{title:{text:'Tekanan Darah (mmHg)',font:{size:10}}},xaxis:{type:'date',tickformat:'%d %b'}}}/>;
}

export function Donut({distribution,total}) {
 return <PlotlyChart height={208} data={[{type:'pie',hole:0.66,sort:false,direction:'clockwise',labels:distribution.map(r=>r.status),values:distribution.map(r=>r.count),marker:{colors:COLORS,line:{color:'#fff',width:2}},textinfo:'none',hovertemplate:'%{label}: %{value} partisipan<extra></extra>'}]} layout={{showlegend:false,margin:{l:5,r:5,t:4,b:4},annotations:[{text:`<b style="font-size:22px;color:${NAVY}">${total}</b><br>Partisipan`,showarrow:false,font:{size:11,color:'#5b6b88'},x:.5,y:.5}]}}/>;
}

export function DistributionLegend({distribution,total}) {return <div className="dist-legend">{distribution.map((r,i)=><div className="leg-row" key={r.status}><span className="leg-dot" style={{background:COLORS[i]}}/><span className="leg-name">{r.status}</span><b>{fmt(r.percent,0)}% <span>({r.count})</span></b></div>)}</div>}

export function AgeBars({items}){return <PlotlyChart height={256} data={['Normal','Pra-hipertensi','Hipertensi'].map((name,i)=>({type:'bar',name,x:items.map(v=>v.age),y:items.map(v=>v[name]),marker:{color:[COLORS[0],COLORS[1],COLORS[2]][i]}}))} layout={{barmode:'group',bargap:.28,legend:legendTop,margin:{l:41,r:5,t:31,b:48},xaxis:{title:{text:'Kelompok Usia',font:{size:10}}},yaxis:{title:{text:'Jumlah Partisipan',font:{size:10}},dtick:1}}}/>}

export function CorrHeatmap({items}){return <PlotlyChart height={256} data={[{type:'heatmap',x:['Sistolik','Diastolik'],y:items.map(x=>x.feature),z:items.map(x=>[x.sistolik,x.diastolik]),zmin:-1,zmax:1,colorscale:[[0,'#5b8def'],[.5,'#fff'],[1,'#f26b6b']],text:items.map(x=>[fmt(x.sistolik,2),fmt(x.diastolik,2)]),texttemplate:'%{text}',textfont:{size:11,color:'#1f2a44'},xgap:2,ygap:2,colorbar:{thickness:10,len:.85},hovertemplate:'%{y} vs %{x}: %{z:.2f}<extra></extra>'}]} layout={{margin:{l:120,r:6,t:4,b:28},xaxis:{showgrid:false},yaxis:{autorange:'reversed',showgrid:false,tickfont:{size:10}}}}/>}

export function ModelDonut({accuracy}){return <PlotlyChart height={174} data={[{type:'pie',hole:.74,sort:false,values:[accuracy,100-accuracy],marker:{colors:['#22b36b','#e1f1e8']},textinfo:'none',hoverinfo:'skip'}]} layout={{showlegend:false,margin:{l:5,r:5,t:0,b:0},annotations:[{text:`Akurasi Model<br><b style="font-size:20px;color:${NAVY}">${fmt(accuracy)}%</b>`,showarrow:false,font:{size:10},x:.5,y:.5}]}}/>}

export function Confusion({matrix}){const [[tn,fp],[fn,tp]]=matrix;return <><div className="kf-title">Matriks Konfusi (contoh)</div><table className="kf"><thead><tr><th/><th/><th colSpan="2">Aktual</th></tr><tr><th/><th/><th>Tidak<br/>Hipertensi</th><th>Hipertensi</th></tr></thead><tbody><tr><th rowSpan="2" className="vert">Prediksi</th><th>Tidak<br/>Hipertensi</th><td className="aman">{tn}</td><td>{fp}</td></tr><tr><th>Hipertensi</th><td>{fn}</td><td className="panas">{tp}</td></tr></tbody></table></>}

export function ModelBars({models,height=203}){const max=Math.max(...models.map(r=>r.accuracy));return <PlotlyChart height={height} data={[{type:'bar',x:models.map(x=>x.model.replace(' ','<br>')),y:models.map(x=>x.accuracy),marker:{color:models.map(x=>x.accuracy===max?'#22b36b':'#b3c8ee')},text:models.map(x=>fmt(x.accuracy,2)),textposition:'outside',cliponaxis:false,width:.5}]} layout={{margin:{l:28,r:5,t:28,b:55},yaxis:{range:[0,1.05],title:{text:'Akurasi',font:{size:10}}},xaxis:{tickfont:{size:9}}}}/>}

export function RangeTrends({trends}){
 const x=trends.map(x=>x.tanggal);
 const traces=[];
 for (const [name,color] of [['sistolik',BIRU],['diastolik',ORANYE]]) {
  traces.push({x,y:trends.map(a=>a[name+'_max']),type:'scatter',mode:'lines',line:{width:0},showlegend:false,hoverinfo:'skip'});
  traces.push({x,y:trends.map(a=>a[name+'_min']),type:'scatter',mode:'lines',fill:'tonexty',fillcolor:color+'22',line:{width:0},name:name[0].toUpperCase()+name.slice(1)+' (rentang)'});
  traces.push({x,y:trends.map(a=>a[name+'_mean']),type:'scatter',mode:'lines+markers',line:{color,width:2.5},marker:{size:4},name:name[0].toUpperCase()+name.slice(1)+' rata-rata'});
 }
 return <PlotlyChart height={424} data={traces} layout={{margin:{l:50,r:12,t:40,b:44},title:{text:'Pergerakan rata-rata dan rentang pengukuran',font:{size:14,color:NAVY}},legend:{orientation:'h',x:0,y:-.2},yaxis:{title:'mmHg'},xaxis:{type:'date',tickformat:'%d %b'}}}/>;
}
