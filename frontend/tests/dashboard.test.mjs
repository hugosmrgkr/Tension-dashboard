import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {build} from 'esbuild';
import React from 'react';
import TestRenderer, {act} from 'react-test-renderer';

// Exercise the real React tree and API helper. Only the browser-only Plotly
// renderer is substituted; the production build separately bundles real Plotly.
const bundled=await build({
  stdin:{contents:"export {default as App} from './src/App.jsx'; export {MiniTable} from './src/components/Common.jsx'; export {Tren} from './src/pages/Pages.jsx'; export {SessionPressureLines} from './src/components/Visuals.jsx';",resolveDir:process.cwd(),loader:'jsx'},
  bundle:true,write:false,platform:'node',format:'cjs',external:['react','react-dom','lucide-react'],
  plugins:[{name:'plotly-renderer-probe',setup(builder){
    builder.onResolve({filter:/^(react-plotly\.js\/factory|plotly\.js-dist-min)$/},args=>({path:args.path,namespace:'probe'}));
    builder.onLoad({filter:/.*/,namespace:'probe'},args=>({loader:'js',contents:args.path.startsWith('react-')?
      "import React from 'react'; export default ()=>props=>React.createElement('plot-probe',props);":"export default {};"}));
  }}],
});
const entry={exports:{}};
new Function('require','module','exports',bundled.outputFiles[0].text)(createRequire(import.meta.url),entry,entry.exports);
const {App,MiniTable,Tren,SessionPressureLines}=entry.exports;
const meta={source_kind:'synthetic',source:'Fixture API',message:'DATA SINTETIS / SIMULASI',warehouse_empty:false,access_restricted:false,
  participants:23,daily_records:77,session_records:151,respondent_ids:['SIM009'],sessions:['Pagi','Malam'],age_groups:[],province:[],city:[],gender:[],occupation:[],min_date:'2026-01-01',max_date:'2026-01-30',etl_audit_version:'cp2-1'};
const payload={empty:false,kpis:{respondents:23,daily_records:77,sessions:151,mean_sbp:123.4,mean_dbp:78.9},comparison:null,
  trend:[{date:'2026-01-01',session:'Pagi',sbp:123.4,dbp:78.9,n:151}],session_box:[{session:'Pagi',sbp_mean:123.4,dbp_mean:78.9}],heatmap:[{date:'2026-01-01',session:'Pagi',sbp:123.4,n:151}],scatter:[],small_multiples:[],
  categories:{salty_food:[],fruit:[],vegetable:[],caffeine:[],activity_type:[]},participants:[],daily_rows:[],session_rows:[],session_stats:[],
  quality:{accepted_profiles:23,accepted_daily:77,rejected_daily:0},filtered_quality:{daily_records:77,session_records:151,incomplete_sessions:0,missing_sleep_hours:2,missing_sitting:1,missing_smoke_count:70}};
const model={available:true,rows_training:12,rows_test:3,scores:[{model:'Baseline',mae:1,rmse:2,r2:.5}],actual_vs_predicted:[],features:['sbp'],split:'ID',limitation:'SIMULASI'};
const rowsCmp=['Naive 7-day mean','Linear Regression','Random Forest','Hist Gradient Boosting'].map((name,i)=>({model:name,kind:i?'terlatih':'baseline naif',validation:{mae:2+i,rmse:2.5+i,r2:.1,n:60},test:{mae:1.5+i,rmse:2+i,r2:null,n:2}}));
const comparison={available:true,artifact_integrity_verified:true,run_id:'RUNCMP1',status:'DATA SINTETIS / SIMULASI - EKSPERIMEN',target_approved:false,horizon_days:7,selected_model:'Linear Regression',
  selection:{rule:'RMSE validasi terkecil',beats_naive_on_validation:false},comparison:rowsCmp,respondents_train:['A','B','C'],respondents_test:['D'],rows_training:60,rows_test:2,cutoff:'2026-09-18',
  dataset:'fixture',split:'ID + waktu',seed:42,validation_folds:4,features:['f1'],limitation:'SINTETIS kecil',warnings:['Test hanya 2 origin: metrik sangat tidak stabil.'],
  actual_vs_predicted:[{respondent_id:'D',actual:120,naive_7_day_mean:119,linear_regression:121,random_forest:122,hist_gradient_boosting:118},{respondent_id:'D',actual:125,naive_7_day_mean:124,linear_regression:123,random_forest:126,hist_gradient_boosting:127}]};
const prediction={respondent_id:'SIM009',last_date:'2026-09-20',forecast_start:'2026-09-21',forecast_end:'2026-09-27',prediction_mmHg:121.5,reference_naive_mmHg:120.1,notes:['Pada validasi, model ini tidak lebih baik dari baseline naif; gunakan angka naif sebagai pembanding.'],model:{algorithm:'Linear Regression',version:'RUNCMP1',trained_on:'2026-11-10',target:'future_7d_mean_sbp',horizon_days:7,data_source:'fixture',target_approved:false}};
let renderer,requests,comparisonOverride;
const visible=node=>typeof node==='string'?node:(node.children||[]).map(visible).join('');
const button=label=>renderer.root.findAllByType('button').find(node=>visible(node)===label);
const text=()=>JSON.stringify(renderer.toJSON());
async function settle(){for(let n=0;n<3;n++)await act(async()=>{await new Promise(resolve=>setImmediate(resolve))});}
async function mount({empty=false,failAnalytics=false,page='Dashboard',dataOverride=null,comparisonData=comparison,requireToken=false}={}){
  requests=[];const store=new Map();comparisonOverride=comparisonData;
  global.window={sessionStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value),removeItem:key=>store.delete(key)},location:{hash:'#'+encodeURIComponent(page)},addEventListener(){},removeEventListener(){},scrollTo(){}};
  global.document={createElement:()=>({click(){},remove(){}}),body:{appendChild(){}}};
  global.URL.createObjectURL=()=> 'blob:test';global.URL.revokeObjectURL=()=>{};
  global.fetch=async(url,options={})=>{
    requests.push({url,method:options.method||'GET',authorization:options.headers?.Authorization});
    if(requireToken&&options.headers?.Authorization!=='Bearer tok-viewer')return {ok:false,status:401,json:async()=>({detail:'Autentikasi diperlukan.'})};
    const failure=failAnalytics&&url.startsWith('/api/analytics');
    return {ok:!failure,status:failure?503:200,blob:async()=>new Blob(['csv']),json:async()=>failure?{detail:'Warehouse tidak dapat dibaca'}:
      url==='/api/meta'?{...meta,warehouse_empty:empty,participants:empty?0:23,message:empty?'Warehouse belum berisi data. Jalankan ETL manual.':meta.message}:
      url==='/api/model/baseline'?model:url==='/api/model/comparison'?comparisonOverride:url.startsWith('/api/model/predict')?prediction:empty?{...payload,empty:true,kpis:{},trend:[]}:dataOverride||payload};
  };
  await act(async()=>{renderer=TestRenderer.create(React.createElement(App))});
  await settle();
}
async function dispose(){if(renderer)await act(async()=>renderer.unmount());renderer=null;}

test('empty warehouse shows a useful message without KPI or plot fixtures',async()=>{
  try{await mount({empty:true});assert.match(text(),/Warehouse belum berisi data/);assert.equal(renderer.root.findAllByType('plot-probe').length,0);assert.equal(renderer.root.findAll(node=>node.props.className==='kpi-value').length,0);assert.ok(!requests.some(r=>r.url.includes('/model/')));}finally{await dispose();}
});

test('dashboard reads arbitrary API values; filters and exports preserve exact ID and session',async()=>{
  try{
    await mount();
    assert.deepEqual(renderer.root.findAll(node=>node.props.className==='kpi-value').map(visible),['23','77','151','123,4 mmHg']);
    // This fixture contains only morning data: the night panel must remain empty.
    assert.equal(renderer.root.findAllByType('plot-probe').length,3);
    assert.match(text(),/Tren Tekanan Darah Pagi/);
    assert.match(text(),/Tren Tekanan Darah Malam/);
    assert.match(text(),/Belum ada nilai valid untuk grafik ini/);
    await act(async()=>renderer.root.findByProps({'aria-label':'ID responden'}).props.onChange({target:{value:'SIM009'}}));await settle();
    await act(async()=>renderer.root.findByProps({'aria-label':'Sesi pengukuran'}).props.onChange({target:{value:'Malam'}}));await settle();
    assert.ok(requests.some(r=>r.url==='/api/analytics?respondent_id=SIM009&session=Malam'));
    await act(async()=>button('Kelola Data').props.onClick());await settle();
    await act(async()=>button('Sesi tensi').props.onClick());await settle();
    assert.ok(requests.some(r=>r.url==='/api/data/export/sessions?respondent_id=SIM009&session=Malam'));
    assert.equal(renderer.root.findAll(node=>node.type==='input'&&node.props.type==='file').length,0);
    assert.ok(requests.every(r=>r.method==='GET'));
    assert.match(text(),/DATA SINTETIS \/ SIMULASI/);
  }finally{await dispose();}
});

test('all eight pages render with API data and baseline remains an explicit artifact experiment',async()=>{
  try{await mount();for(const page of ['Data Partisipan','Analisis Faktor Risiko','Tren Tekanan Darah','Prediksi Tekanan Darah','Evaluasi Model','Laporan & Ringkasan','Kelola Data','Dashboard']){
    await act(async()=>button(page).props.onClick());await settle();assert.equal(renderer.root.findByType('h1').children.join(''),page);
  }}finally{await dispose();}
});

test('analytics failure remains visible while evaluation and management can still open',async()=>{
  try{await mount({failAnalytics:true});assert.match(text(),/Gagal membaca data/);assert.equal(renderer.root.findAllByType('plot-probe').length,0);
    await act(async()=>button('Evaluasi Model').props.onClick());await settle();assert.match(text(),/Tabel metrik perbandingan/);
    await act(async()=>button('Kelola Data').props.onClick());await settle();assert.match(text(),/Sumber aktif/);assert.match(text(),/Kualitas pilihan belum dapat dibaca/);
  }finally{await dispose();}
});

test('pagination exposes rows past the old 200-row cut-off and preserves nulls',async()=>{
  try{
    const rows=Array.from({length:225},(_,i)=>({id:`ID${i+1}`,value:null}));
    await act(async()=>{renderer=TestRenderer.create(React.createElement(MiniTable,{columns:[['id','ID'],['value','Value']],rows}))});
    for(let n=0;n<8;n++)await act(async()=>renderer.root.findByProps({'aria-label':'Halaman berikutnya'}).props.onClick());
    assert.match(text(),/ID225/);assert.ok(!renderer.root.findAllByType('td').some(node=>visible(node)==='0'));
  }finally{await dispose();}
});

test('incomplete sessions remain in the raw table without fabricated charts',async()=>{
  try{await act(async()=>{renderer=TestRenderer.create(React.createElement(Tren,{data:{...payload,empty:true,message:'Sesi belum lengkap',session_rows:[{respondent_id:'SIM009',date:'2026-01-01',session:'Malam',is_valid:false,sbp1:null,dbp1:null}]}}))});
    assert.match(text(),/Tidak lengkap/);assert.match(text(),/SIM009/);assert.equal(renderer.root.findAllByType('plot-probe').length,0);
  }finally{await dispose();}
});

test('clicking a trend point applies date/session globally and reset clears it',async()=>{
  try{
    await mount();
    const plot=renderer.root.findAllByType('plot-probe').find(node=>node.props.data[0]?.type==='scatter');
    await act(async()=>plot.props.onClick({points:[{customdata:[151,'2026-01-01','Pagi']}]}));await settle();
    assert.ok(requests.some(row=>row.url==='/api/analytics?start_date=2026-01-01&end_date=2026-01-01&session=Pagi'));
    assert.equal(renderer.root.findByProps({'aria-label':'Sesi pengukuran'}).props.value,'Pagi');
    await act(async()=>button('Reset filter').props.onClick());await settle();
    assert.equal(requests.filter(row=>row.url.startsWith('/api/analytics')).at(-1).url,'/api/analytics');
  }finally{await dispose();}
});

test('date errors prevent incompatible analytics requests and never retain old KPI',async()=>{
  try{
    await mount();
    await act(async()=>renderer.root.findByProps({'aria-label':'Mulai tanggal'}).props.onChange({target:{value:'2026-01-20'}}));await settle();
    const count=requests.length;
    await act(async()=>renderer.root.findByProps({'aria-label':'Sampai tanggal'}).props.onChange({target:{value:'2026-01-01'}}));await settle();
    assert.match(text(),/Tanggal mulai harus sebelum/);
    assert.equal(requests.length,count);
    assert.equal(renderer.root.findAll(node=>node.props.className==='kpi-value').length,0);
  }finally{await dispose();}
});

test('risk page explains smoking, medication, nulls and observed sample sizes',async()=>{
  try{
    await mount({page:'Analisis Faktor Risiko'});
    assert.match(text(),/Status merokok dan SBP harian/);
    assert.match(text(),/Kepatuhan obat dan SBP harian/);
    assert.match(text(),/Tidak menggunakan obat tidak sama dengan tidak patuh/);
    assert.match(text(),/Belum ada nilai valid untuk grafik/);
    assert.match(text(),/Pearson r/);
  }finally{await dispose();}
});

test('daily-active respondents remain visible without valid BP and no fake chart appears',async()=>{
  try{
    await mount({dataOverride:{...payload,empty:false,message:'Belum ada sesi yang lolos gate pasangan.',kpis:{respondents:23,respondents_with_valid_bp:0,daily_records:77,sessions:0,mean_sbp:null},trend:[],session_box:[],heatmap:[],filtered_quality:{...payload.filtered_quality,valid_sessions:0,pending_review_sessions:151}}});
    const values=renderer.root.findAll(node=>node.props.className==='kpi-value').map(visible);
    assert.deepEqual(values.slice(0,3),['23','77','0']);
    assert.ok(!values[3].startsWith('0'));assert.equal(renderer.root.findAllByType('plot-probe').length,0);
    assert.match(text(),/catatan harian diterima ETL/);assert.match(text(),/Sesi pending review/);
  }finally{await dispose();}
});

test('P2-03 evaluation reads the verified comparison artifact: metrics, warnings, no invented numbers',async()=>{
  try{
    await mount();await act(async()=>button('Evaluasi Model').props.onClick());await settle();
    const page=text();
    assert.match(page,/Tabel metrik perbandingan/);assert.match(page,/Random Forest/);assert.match(page,/Hist Gradient Boosting/);
    assert.match(page,/Test hanya 2 origin/);assert.match(page,/RUNCMP1/);assert.match(page,/Belum disetujui|belum disetujui dosen/);
    assert.ok(requests.some(r=>r.url==='/api/model/comparison'));
    assert.ok(renderer.root.findAllByType('plot-probe').length>=5);
  }finally{await dispose();}
});

test('P2-03 evaluation falls back to CP3 baseline when comparison artifact is unavailable',async()=>{
  try{
    await mount({comparisonData:{available:false,message:'Artefak perbandingan belum tersedia'}});
    await act(async()=>button('Evaluasi Model').props.onClick());await settle();
    assert.match(text(),/Tabel metrik eksperimen/);assert.doesNotMatch(text(),/Tabel metrik perbandingan/);
  }finally{await dispose();}
});

test('P2-02 prediction page calls the trained-model endpoint and shows model metadata and naive reference',async()=>{
  try{
    await mount();await act(async()=>button('Prediksi Tekanan Darah').props.onClick());await settle();
    await act(async()=>renderer.root.findByType('form').props.onSubmit({preventDefault(){}}));await settle();
    assert.ok(requests.some(r=>r.url==='/api/model/predict?respondent_id=SIM009'&&r.method==='GET'));
    const shown=visible(renderer.root.findAll(node=>node.props.className==='prediction-result')[0]);
    assert.match(shown,/121,50 mmHg/);assert.match(shown,/120,10 mmHg/);assert.match(shown,/Linear Regression/);assert.match(shown,/tidak lebih baik dari baseline naif/);
  }finally{await dispose();}
});

test('P2-04 KPI cards expose written definition, unit, grain and sample size from the API',async()=>{
  const defs={respondents:{formula:'COUNT DISTINCT id',unit:'ID',grain:'ID responden',filters:'semua'},daily_records:{formula:'COUNT harian',unit:'catatan',grain:'ID x tanggal',filters:'semua'},sessions:{formula:'COUNT sesi valid',unit:'sesi',grain:'ID x tanggal x sesi',filters:'semua'},mean_sbp:{formula:'AVG sbp',unit:'mmHg',grain:'sesi',filters:'semua'}};
  try{
    await mount({dataOverride:{...payload,kpi_definitions:defs,comparison_definition:'Periode pembanding sebelumnya sama panjang.'}});
    const panels=renderer.root.findAll(node=>node.props.className==='kpi-def').map(visible);
    assert.equal(panels.length,4);
    assert.match(panels[2],/COUNT sesi valid/);assert.match(panels[2],/ID x tanggal x sesi/);assert.match(panels[0],/151|23/);
    assert.match(text(),/Periode pembanding sebelumnya sama panjang/);
  }finally{await dispose();}
});

test('P2-06 without a token the app asks to sign in; the token is sent as Bearer and kept only in sessionStorage',async()=>{
  try{
    await mount({requireToken:true});
    assert.match(visible(renderer.root.findAll(node=>node.props.className==='notice notice-warning')[0]),/Masuk diperlukan/);
    assert.equal(renderer.root.findAllByType('plot-probe').length,0);
    await act(async()=>renderer.root.findByProps({'aria-label':'Token akses'}).props.onChange({target:{value:'tok-viewer'}}));
    await act(async()=>renderer.root.findByType('form').props.onSubmit({preventDefault(){}}));await settle();
    assert.ok(requests.some(r=>r.url==='/api/meta'&&r.authorization==='Bearer tok-viewer'));
    assert.ok(requests.some(r=>r.url.startsWith('/api/analytics')&&r.authorization==='Bearer tok-viewer'));
    assert.doesNotMatch(text(),/Masuk diperlukan/);
    assert.ok(requests.every(r=>!r.url.includes('tok-viewer')));
  }finally{await dispose();}
});


test('session trend compares SBP and DBP together, isolates morning/night and preserves click filters and missing values',()=>{
 const rows=[
  {date:'2026-09-02',session:'Pagi',sbp:125,dbp:null,n:2},
  {date:'2026-09-01',session:'Malam',sbp:130,dbp:84,n:3},
  {date:'2026-09-01',session:'Pagi',sbp:120,dbp:80,n:4}
 ];
 for(const session of ['Pagi','Malam']){
  let selected;
  const chart=TestRenderer.create(React.createElement(SessionPressureLines,{rows,session,onSelect:value=>selected=value}));
  const plot=chart.root.findByType('plot-probe').props;
  assert.deepEqual(plot.data.map(trace=>trace.name),['SBP','DBP']);
  assert.deepEqual(plot.data[0].y,session==='Pagi'?[120,125]:[130]);
  assert.deepEqual(plot.data[1].y,session==='Pagi'?[80,null]:[84]);
  assert.equal(plot.data[1].connectgaps,false);
  assert.equal(plot.layout.yaxis.title,'Rata-rata tekanan darah (mmHg)');
  for(const trace of plot.data){
   plot.onClick({points:[{customdata:trace.customdata[0]}]});
   assert.deepEqual(selected,{start_date:'2026-09-01',end_date:'2026-09-01',session});
  }
  chart.unmount();
 }
 const empty=TestRenderer.create(React.createElement(SessionPressureLines,{rows:rows.filter(row=>row.session==='Pagi'),session:'Malam'}));
 assert.equal(empty.root.findAllByType('plot-probe').length,0);
 assert.match(JSON.stringify(empty.toJSON()),/Belum ada nilai valid/);
 empty.unmount();
});
