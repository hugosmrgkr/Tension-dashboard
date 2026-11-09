import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {build} from 'esbuild';
import React from 'react';
import TestRenderer, {act} from 'react-test-renderer';

// Exercise the real React tree and API helper. Only the browser-only Plotly
// renderer is substituted; the production build separately bundles real Plotly.
const bundled=await build({
  stdin:{contents:"export {default as App} from './src/App.jsx'; export {MiniTable} from './src/components/Common.jsx'; export {Tren} from './src/pages/Pages.jsx';",resolveDir:process.cwd(),loader:'jsx'},
  bundle:true,write:false,platform:'node',format:'cjs',external:['react','react-dom','lucide-react'],
  plugins:[{name:'plotly-renderer-probe',setup(builder){
    builder.onResolve({filter:/^(react-plotly\.js\/factory|plotly\.js-dist-min)$/},args=>({path:args.path,namespace:'probe'}));
    builder.onLoad({filter:/.*/,namespace:'probe'},args=>({loader:'js',contents:args.path.startsWith('react-')?
      "import React from 'react'; export default ()=>props=>React.createElement('plot-probe',props);":"export default {};"}));
  }}],
});
const entry={exports:{}};
new Function('require','module','exports',bundled.outputFiles[0].text)(createRequire(import.meta.url),entry,entry.exports);
const {App,MiniTable,Tren}=entry.exports;
const meta={source_kind:'synthetic',source:'Fixture API',message:'DATA SINTETIS / SIMULASI',warehouse_empty:false,access_restricted:false,
  participants:23,daily_records:77,session_records:151,respondent_ids:['SIM009'],sessions:['Pagi','Malam'],age_groups:[],province:[],city:[],gender:[],occupation:[],min_date:'2026-01-01',max_date:'2026-01-30',etl_audit_version:'cp2-1'};
const payload={empty:false,kpis:{respondents:23,daily_records:77,sessions:151,mean_sbp:123.4,mean_dbp:78.9},comparison:null,
  trend:[{date:'2026-01-01',session:'Pagi',sbp:123.4,dbp:78.9,n:151}],session_box:[{session:'Pagi',sbp_mean:123.4,dbp_mean:78.9}],heatmap:[{date:'2026-01-01',session:'Pagi',sbp:123.4,n:151}],scatter:[],small_multiples:[],
  categories:{salty_food:[],fruit:[],vegetable:[],caffeine:[],activity_type:[]},participants:[],daily_rows:[],session_rows:[],session_stats:[],
  quality:{accepted_profiles:23,accepted_daily:77,rejected_daily:0},filtered_quality:{daily_records:77,session_records:151,incomplete_sessions:0,missing_sleep_hours:2,missing_sitting:1,missing_smoke_count:70}};
const model={available:true,rows_training:12,rows_test:3,scores:[{model:'Baseline',mae:1,rmse:2,r2:.5}],actual_vs_predicted:[],features:['sbp'],split:'ID',limitation:'SIMULASI'};
let renderer,requests;
const visible=node=>typeof node==='string'?node:(node.children||[]).map(visible).join('');
const button=label=>renderer.root.findAllByType('button').find(node=>visible(node)===label);
const text=()=>JSON.stringify(renderer.toJSON());
async function settle(){for(let n=0;n<3;n++)await act(async()=>{await new Promise(resolve=>setImmediate(resolve))});}
async function mount({empty=false,failAnalytics=false,page='Dashboard',dataOverride=null}={}){
  requests=[];
  global.window={location:{hash:'#'+encodeURIComponent(page)},addEventListener(){},removeEventListener(){},scrollTo(){}};
  global.document={createElement:()=>({click(){},remove(){}}),body:{appendChild(){}}};
  global.URL.createObjectURL=()=> 'blob:test';global.URL.revokeObjectURL=()=>{};
  global.fetch=async(url,options={})=>{
    requests.push({url,method:options.method||'GET'});
    const failure=failAnalytics&&url.startsWith('/api/analytics');
    return {ok:!failure,status:failure?503:200,blob:async()=>new Blob(['csv']),json:async()=>failure?{detail:'Warehouse tidak dapat dibaca'}:
      url==='/api/meta'?{...meta,warehouse_empty:empty,participants:empty?0:23,message:empty?'Warehouse belum berisi data. Jalankan ETL manual.':meta.message}:
      url==='/api/model/baseline'?model:empty?{...payload,empty:true,kpis:{},trend:[]}:dataOverride||payload};
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
    assert.equal(renderer.root.findAllByType('plot-probe').length,4);
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
  try{await mount();for(const page of ['Data Partisipan','Analisis Faktor Risiko','Tren Tekanan Darah','Prediksi Hipertensi','Evaluasi Model','Laporan & Ringkasan','Kelola Data','Dashboard']){
    await act(async()=>button(page).props.onClick());await settle();assert.equal(renderer.root.findByType('h1').children.join(''),page);
  }}finally{await dispose();}
});

test('analytics failure remains visible while evaluation and management can still open',async()=>{
  try{await mount({failAnalytics:true});assert.match(text(),/Gagal membaca data/);assert.equal(renderer.root.findAllByType('plot-probe').length,0);
    await act(async()=>button('Evaluasi Model').props.onClick());await settle();assert.match(text(),/Tabel metrik eksperimen/);
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
