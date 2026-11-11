import React,{useEffect,useRef,useState} from 'react';
import {Activity,ArrowRight,BookOpen,Database,Download,FileCheck2,HeartPulse,Target,UsersRound,CalendarDays} from 'lucide-react';
import {Card,Notice,MiniTable,Empty,Loading} from '../components/Common';
import {SessionPressureLines,SessionLines,SessionBox,SessionHeatmap,NumericScatter,StressBox,CategoryBars,PieCategories,WorkTreemap,SmallMultiples,ModelComparison,ActualVsPredicted,ResidualPlot,CountBars,Histogram,ValidationVsTest,ResidualHistogram} from '../components/Visuals';
import {api,fmt,whole,queryString,download} from '../lib/api';

function Explainer({children}){return <p className="chart-explainer">{children}</p>}
function ChartCard({title,sample,description,children}){return <Card title={title} className="analysis-card">{sample&&<p className="sample-note">{sample}</p>}{children}<Explainer>{description}</Explainer></Card>}
const dailySample=rows=>`${whole(rows.length)} ID-tanggal dari ${whole(new Set(rows.map(row=>row.respondent_id)).size)} ID`;
const categorySample=rows=>`${whole((rows||[]).reduce((sum,row)=>sum+row.n,0))} catatan harian valid; jumlah ID tiap kategori pada tooltip`;
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
export function Dashboard({data,go,onFilter}){
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
export function DataPartisipan({data,onFilter}){
 const [search,setSearch]=useState('');
 const profiles=data?.participants||[],groups=data?.demographics||{};
 const rows=profiles.filter(row=>[row.respondent_id,row.city,row.occupation,row.province,row.education].join(' ').toLowerCase().includes(search.toLowerCase()));
 if(!data)return <Empty/>;
 if(!profiles.length)return <Empty message={data.message}/>;
 return <><Notice>Profil dihitung satu kali per ID, bukan per sesi. Grafik mengikuti filter global; pencarian di bawah hanya menyaring tabel. Nama, kontak, dan identitas langsung tidak ditampilkan.</Notice>
 <p className="interaction-hint">Klik jenis kelamin, pendidikan, pekerjaan atau wilayah untuk menyaring semua analitik. Wilayah dapat diperinci dari provinsi ke kabupaten/kota.</p>
 <div className="page-grid two">
 <ChartCard title="Distribusi usia responden" sample={`${whole(profiles.filter(row=>Number.isFinite(row.age)).length)} profil dengan usia`} description="Usia dalam tahun pada Form Awal. Setiap profil menyumbang satu observasi; nilai kosong tidak digambar."><Histogram rows={profiles} field="age" label="Usia" unit="tahun"/></ChartCard>
 <ChartCard title="Komposisi jenis kelamin" sample={`${whole(profiles.length)} profil pada pilihan global`} description="Proporsi profil pada jawaban formulir; bukan proporsi sesi pengukuran."><PieCategories rows={groups.gender} unit="responden" onSelect={onFilter?value=>onFilter({gender:value}):undefined}/></ChartCard>
 <ChartCard title="Pendidikan responden" sample={`${whole(profiles.length)} profil`} description="Jumlah ID per tingkat pendidikan. Klik kategori untuk memeriksa pola pengukuran kelompok tersebut."><CountBars rows={groups.education} onSelect={onFilter?value=>onFilter({education:value}):undefined}/></ChartCard>
 <ChartCard title="Pekerjaan responden" sample={`${whole(profiles.length)} profil`} description="Pekerjaan berasal dari Form Awal. Kelompok kecil harus dibaca bersama jumlah sampelnya."><CountBars rows={groups.occupation} onSelect={onFilter?value=>onFilter({occupation:value}):undefined}/></ChartCard>
 <ChartCard title="Sebaran responden menurut provinsi" sample={`${whole(profiles.length)} profil`} description="Klik provinsi, lalu perinci pada grafik kabupaten/kota. Sebaran ini tidak mewakili cakupan populasi wilayah."><CountBars rows={groups.province} onSelect={onFilter?value=>onFilter({province:value,city:''}):undefined}/></ChartCard>
 <ChartCard title="Sebaran responden menurut kabupaten/kota" sample={`${whole(profiles.length)} profil`} description="Lokasi sesuai jawaban formulir, tanpa koordinat atau alamat pribadi."><CountBars rows={groups.city} onSelect={onFilter?value=>onFilter({city:value}):undefined}/></ChartCard>
 <ChartCard title="Distribusi BMI responden" sample={`${whole(profiles.filter(row=>Number.isFinite(row.bmi)).length)} profil dengan BMI`} description="BMI = berat badan (kg) / tinggi (m) kuadrat. Grafik deskriptif ini tidak memberikan kategori atau diagnosis klinis."><Histogram rows={profiles} field="bmi" label="BMI" unit="kg/m2"/></ChartCard>
 <ChartCard title="Kelompok usia responden" sample={`${whole(profiles.length)} profil`} description="Kelompok usia mengikuti definisi API. Klik kelompok untuk menyaring KPI, faktor gaya hidup dan tren."><CountBars rows={groups.age_group} onSelect={onFilter?value=>onFilter({age_group:value}):undefined}/></ChartCard>
 </div>
 <Card title="Profil responden anonim" action={<span className="hint-inline">{whole(rows.length)} dari {whole(profiles.length)} profil</span>}><div className="table-toolbar"><label className="field"><span>Cari ID, lokasi, pendidikan, atau pekerjaan</span><input value={search} onChange={event=>setSearch(event.target.value)} placeholder="Cari pada tabel terfilter"/></label></div>
 <MiniTable rows={rows.map(row=>({...row,bmi:fmt(row.bmi,1),days:whole(row.days),drill:onFilter?<button className="link-button" onClick={()=>onFilter({respondent_id:row.respondent_id})} aria-label={'Telusuri '+row.respondent_id}>Telusuri ID</button>:null}))} columns={[["respondent_id","ID"],["age","Usia (tahun)"],["gender","Jenis kelamin"],["education","Pendidikan"],["occupation","Pekerjaan"],["province","Provinsi"],["city","Kab/Kota"],["bmi","BMI (kg/m2)"],["active_days_week","Hari aktif/minggu"],["days","Hari tercatat"],["drill","Perinci"]]}/><Explainer>Hari tercatat adalah tanggal unik pada filter aktif. Profil tidak digandakan untuk sesi pagi dan malam. Data profil kosong tetap ditampilkan sebagai tanda kosong.</Explainer></Card></>;
}
export function FaktorRisiko({data,onFilter}){
 if(!data||data.empty||data.kpis.sessions===0)return <Empty message={data?.message}/>;
 const d=data.scatter,c=data.categories;
 const numeric=(field)=>d.filter(row=>Number.isFinite(row[field])&&Number.isFinite(row.sbp_mean));
 const category=(field,title,description)=><ChartCard key={field} title={title} sample={categorySample(c[field])} description={description}><CategoryBars rows={c[field]}/></ChartCard>;
 return <><Notice>Semua hubungan adalah asosiasi deskriptif, bukan sebab-akibat. Pengamatan berulang dari ID yang sama saling berkaitan; grafik tidak menguji efek klinis. Missing dikeluarkan hanya dari grafik yang membutuhkan kolom tersebut.</Notice>
 <p className="interaction-hint">Klik titik scatter untuk memperinci ID dan tanggal melalui filter global; semua grafik dan ekspor ikut berubah.</p><div className="page-grid two">
 <ChartCard title="Durasi tidur dan SBP harian" sample={dailySample(numeric('sleep_hours'))} description="Durasi tidur dalam jam. Interpretasi HH:MM hanya berlaku untuk sumber sintetis sesuai CP2; pola titik tidak menunjukkan pengaruh kausal."><NumericScatter rows={d} xkey="sleep_hours" xlabel="Tidur (jam)" onSelect={onFilter}/></ChartCard>
 <ChartCard title="SBP harian menurut tingkat stres" sample={dailySample(numeric('stress'))} description="Skala stres 1 sampai 5. Bandingkan distribusi, bukan hanya median; jumlah catatan tiap tingkat dapat berbeda."><StressBox rows={d}/></ChartCard>
 <ChartCard title="Aktivitas fisik dan SBP harian" sample={dailySample(numeric('activity_minutes'))} description="Aktivitas dalam menit per hari. Nol yang benar-benar dijawab tetap valid; missing tidak diubah menjadi nol."><NumericScatter rows={d} xkey="activity_minutes" xlabel="Aktivitas (menit/hari)" onSelect={onFilter}/></ChartCard>
 <ChartCard title="Distribusi DBP menurut kelompok usia" sample={`${whole(data.session_box.length)} sesi valid`} description="Violin merangkum bentuk distribusi DBP sesi; kotak di dalamnya menunjukkan kuartil. Ukuran kelompok tidak sama."><SessionBox rows={data.session_box} group="age_group" field="dbp_mean" violin/></ChartCard>
 {category('salty_food','Makanan asin dan SBP harian','Kategori frekuensi sesuai formulir. Perbedaan rerata antar-kategori dapat dipengaruhi usia, obat, dan komposisi ID.')}
 <ChartCard title="Komposisi konsumsi buah" sample={categorySample(c.fruit)} description="Proporsi ID-tanggal dengan jawaban buah dan SBP harian valid, bukan persentase responden unik. Missing tidak masuk penyebut."><PieCategories rows={c.fruit}/></ChartCard>
 <ChartCard title="Komposisi konsumsi sayur" sample={categorySample(c.vegetable)} description="Proporsi catatan harian terukur menurut kategori porsi sayur. Data ini tidak mengukur efek diet secara terkontrol."><PieCategories rows={c.vegetable}/></ChartCard>
 <ChartCard title="Jenis aktivitas pada catatan harian" sample={categorySample(c.activity_type)} description="Luas bidang = jumlah ID-tanggal dengan kategori aktivitas dan SBP valid. Satu jawaban harian tidak digandakan menjadi dua sesi."><WorkTreemap rows={c.activity_type}/></ChartCard>
 {category('caffeine','Kafein dan SBP harian','Kategori jumlah gelas/cangkir sesuai jawaban formulir; n hari dan jumlah ID terlihat pada tooltip.')}
 {category('smoked','Status merokok dan SBP harian','Tidak berlaku karena tidak merokok tetap kategori tersendiri. Missing jumlah merokok tidak berarti nol.')}
 <ChartCard title="Jumlah merokok dan SBP harian" sample={dailySample(numeric('smoke_count'))} description="Jumlah sesuai isian harian, bukan asumsi jumlah batang. Hanya pasangan lengkap ditampilkan; banyak missing membatasi interpretasi."><NumericScatter rows={d} xkey="smoke_count" xlabel="Jumlah merokok (kali/hari)" onSelect={onFilter}/></ChartCard>
 {category('medication','Kepatuhan obat dan SBP harian','Tidak menggunakan obat tidak sama dengan tidak patuh. Kategori berbeda tidak boleh ditafsirkan sebagai bukti efek obat.')}
 {category('sitting','Waktu duduk dan SBP harian','Durasi duduk adalah kategori pada formulir, bukan angka jam kontinu. Bandingkan rerata bersama ukuran tiap kelompok.')}
 <ChartCard title="Tren SBP menurut kelompok usia" sample={`${whole(data.kpis.sessions)} sesi valid`} description="Small multiples memakai rentang sumbu SBP yang sama agar pola antar-kelompok bisa dibandingkan. Rerata per tanggal dapat berganti komposisi ID."><SmallMultiples rows={data.small_multiples}/></ChartCard>
 </div><Card title="Asosiasi numerik pada filter aktif"><MiniTable rows={(data.correlations||[]).map(row=>({...row,field:({sleep_hours:'Tidur (jam)',stress:'Stres (1-5)',activity_minutes:'Aktivitas (menit)',smoke_count:'Jumlah merokok'})[row.field],r:fmt(row.r,3)}))} columns={[["field","Variabel vs SBP harian"],["n","Pasangan ID-tanggal"],["respondents","ID unik"],["r","Pearson r"]]}/><Explainer>r berada pada -1 sampai 1 dan hanya merangkum hubungan linear. Tidak dihitung bila sampel kurang dari 3 atau salah satu variabel konstan. Ini bukan uji signifikansi atau bukti sebab-akibat.</Explainer></Card></>;
}
export function Tren({data,onFilter,filters={}}){
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

export function Prediksi({meta,model,modelLoading}){
 const [rid,setRid]=useState(''),[result,setResult]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 const request=useRef(null),sequence=useRef(0);
 const ids=JSON.stringify(meta?.respondent_ids||[]);
 useEffect(()=>{setRid(JSON.parse(ids)[0]||'');setResult(null);setError('');setLoading(false);sequence.current++;request.current?.abort()},[ids]);
 useEffect(()=>()=>{sequence.current++;request.current?.abort()},[]);
 function choose(value){sequence.current++;request.current?.abort();setRid(value);setResult(null);setError('');setLoading(false)}
 async function submit(event){
  event.preventDefault();if(!rid)return;
  request.current?.abort();const controller=new AbortController(),serial=++sequence.current;request.current=controller;
  setError('');setLoading(true);setResult(null);
  try{const response=await api('/model/predict?respondent_id='+encodeURIComponent(rid),{signal:controller.signal});if(serial===sequence.current)setResult(response)}
  catch(err){if(serial===sequence.current&&err.name!=='AbortError')setError(err.message)}
  finally{if(serial===sequence.current)setLoading(false)}
 }
 const m=result?.model;
 return <><Notice tone="warning"><strong>Model eksperimen - DATA SINTETIS / SIMULASI.</strong> Memperkirakan rerata sistolik tujuh hari berikutnya (mmHg), bukan klasifikasi hipertensi atau diagnosis. Target belum disetujui dosen (target_approved=false).</Notice>
 {modelLoading&&<Loading/>}
 {!modelLoading&&!model?.available&&<Notice tone="warning">{model?.message||'Artefak model belum tersedia. Tidak ada perkiraan contoh yang diisi otomatis.'}</Notice>}
 <div className="page-grid two"><Card title="Input: riwayat responden simulasi" icon={Target}><form className="predict-form" onSubmit={submit}><label className="field"><span>ID responden simulasi</span><select aria-label="ID prediksi model" value={rid} onChange={event=>choose(event.target.value)}>{(meta?.respondent_ids||[]).map(id=><option key={id} value={id}>{id}</option>)}</select></label>
 <p className="muted">Model memerlukan tujuh hari kalender berturut-turut pada akhir riwayat ID. Anda memilih riwayat yang sudah ada di PostgreSQL; fitur dihitung server dengan rumus yang sama seperti saat training.</p>
 <button className="button primary" type="submit" disabled={loading||modelLoading||!rid||!model?.available}>{loading?'Menghitung...':'Hitung perkiraan model'}</button></form>
 {error&&<Notice tone="error">{error}. Periksa kelengkapan riwayat ID, lalu coba lagi.</Notice>}
 <div aria-live="polite">{result&&<div className="prediction-result"><span>Output: estimasi rerata SBP tujuh hari berikutnya</span><strong className="prediction-number">{fmt(result.prediction_mmHg,2)} mmHg</strong><small>ID {result.respondent_id} | Akhir riwayat {result.last_date}</small>{result.forecast_start&&<small>Rentang estimasi {result.forecast_start} sampai {result.forecast_end}</small>}<small>Pembanding baseline naif (rerata 7 hari terakhir): {fmt(result.reference_naive_mmHg,2)} mmHg</small><p>Model: {m?.algorithm} (versi {m?.version}). Tidak disertai interval keyakinan dan tidak digunakan untuk keputusan medis.</p>{(result.notes||[]).map(note=><Notice key={note} tone="warning">{note}</Notice>)}</div>}</div></Card>
 <Card title="Cara membaca prediksi" icon={BookOpen}><div className="guide-steps"><div><b>1</b><span>Pilih ID dengan sedikitnya tujuh hari berurutan. Riwayat terakhir ditentukan oleh tanggal data, bukan tanggal komputer.</span></div><div><b>2</b><span>Server memakai gate pasangan BP yang sama dengan analitik, menghitung fitur histori, lalu menjalankan model terlatih terverifikasi hash.</span></div><div><b>3</b><span>Bandingkan dengan angka baseline naif. Bila model tidak lebih baik dari naif pada validasi, peringatan ditampilkan di atas.</span></div></div>
 {m&&<dl className="model-meta"><dt>Algoritma</dt><dd>{m.algorithm}</dd><dt>Target / horizon</dt><dd>{m.target} / {m.horizon_days} hari</dd><dt>Dilatih pada</dt><dd>{m.trained_on} - {m.data_source}</dd><dt>Status target</dt><dd>{m.target_approved?'Disetujui':'Belum disetujui dosen'}</dd></dl>}
 <Explainer>Eksperimen pada data sintetis; tidak membuktikan performa pada responden asli. Aturan ilmiah final menunggu dosen.</Explainer></Card></div></>;
}
function EvaluasiBaseline({model,modelLoading}){
 if(modelLoading)return <Loading/>;
 if(!model?.available)return <Notice tone="warning">{model?.message||'Hasil baseline belum tersedia atau dataset aktif bukan sintetis. Tidak ada metrik contoh.'}</Notice>;
 const predictions=model.actual_vs_predicted||[],scores=model.scores||[];
 return <><Notice tone="warning">Evaluasi eksperimen <strong>DATA SINTETIS / SIMULASI</strong>. Metrik dibaca melalui API dari artefak eksperimen, bukan evaluasi ulang filter aktif atau bukti performa pada responden asli. Dua pendekatan awal bukan hasil final tiga algoritma.</Notice>
 <div className="metrics-overview"><div><span>Target regresi</span><b>Rerata SBP 7 hari berikutnya (mmHg)</b></div><div><span>Baris training</span><b>{whole(model.rows_training)}</b></div><div><span>Baris test</span><b>{whole(model.rows_test)}</b></div><div><span>Pemisahan data</span><b>ID terpisah + batas waktu + target uji tidak overlap</b></div></div>
 <div className="page-grid two">
 <ChartCard title="Perbandingan MAE metode awal" sample={`${whole(model.rows_test)} baris test pada artefak`} description="MAE adalah rata-rata besar kesalahan absolut dalam mmHg; lebih kecil lebih baik. Ini bukan akurasi persen."><ModelComparison model={model}/></ChartCard>
 <Card title="Tabel metrik eksperimen"><MiniTable rows={scores.map(row=>({...row,mae:fmt(row.mae,3),rmse:fmt(row.rmse,3),r2:fmt(row.r2,3)}))} columns={[["model","Metode"],["mae","MAE (mmHg)"],["rmse","RMSE (mmHg)"],["r2","R2"]]}/><Explainer>RMSE memberi bobot lebih besar pada error besar. R2 membandingkan variasi yang dijelaskan terhadap prediksi rerata; dapat negatif dan bukan persentase akurasi. Baseline naif dibandingkan dengan Linear Regression.</Explainer></Card>
 <ChartCard title="Aktual vs prediksi Linear Regression" sample={`${whole(predictions.length)} pasangan yang tersimpan pada artefak`} description="Titik dekat garis prediksi = aktual menunjukkan error lebih kecil. Rentang garis dihitung dari pasangan hasil, bukan batas tekanan darah buatan."><ActualVsPredicted model={model}/></ChartCard>
 <ChartCard title="Residual prediksi Linear Regression" sample={`${whole(predictions.length)} pasangan pada artefak`} description="Residual = aktual - prediksi dalam mmHg. Nilai positif berarti prediksi terlalu rendah; pola atau sebaran lebar perlu ditinjau pada eksperimen lanjutan."><ResidualPlot model={model}/></ChartCard>
 </div><Card title="Batas eksperimen dan rencana setelah CP3"><p><b>Split:</b> {model.split}. ID train dan test dipisahkan.</p>{model.run_id&&<p><b>Run artefak:</b> {model.run_id}; cutoff {model.cutoff}. Target belum disetujui dosen.</p>}{model.warehouse_batch_match!==true&&<Notice tone="warning">Fingerprint batch warehouse belum cocok atau belum tersedia. Metrik ini tetap milik eksperimen tersimpan, bukan evaluasi ulang data aktif.</Notice>}<Notice tone="warning">Ukuran test {whole(model.rows_test)} origin. Baca bersama jumlah ID dan split; hasil sintetis ini tidak membuktikan generalisasi atau validitas klinis.</Notice><p><b>Fitur tersimpan:</b> {(model.features||[]).join(', ')||'Tidak tersedia'}.</p><p><b>Keterbatasan:</b> {model.limitation}</p><Explainer>Setelah definisi target dan kelayakan data aktual disetujui: tambah algoritma, tuning, validasi dan error analysis. Tahap ini tidak melatih ulang model atau mengklaim model terbaik final.</Explainer></Card></>;
}
const columnKey=name=>name.toLowerCase().replace(/[ -]/g,'_');
const nf=(value,digits=3)=>value==null?'Tidak tersedia':fmt(value,digits);
export function Evaluasi({model,modelLoading,comparison,comparisonLoading}){
 if(comparisonLoading)return <Loading/>;
 if(!comparison?.available)return <EvaluasiBaseline model={model} modelLoading={modelLoading}/>;
 const rows=comparison.comparison,selected=comparison.selected_model,key=columnKey(selected),predictions=comparison.actual_vs_predicted||[];
 const byId=Object.values(predictions.reduce((acc,row)=>{const item=acc[row.respondent_id]||(acc[row.respondent_id]={respondent_id:row.respondent_id,n:0,abs:0,naive:0});item.n++;item.abs+=Math.abs(row.actual-row[key]);item.naive+=Math.abs(row.actual-row[columnKey(rows[0].model)]);return acc},{})).map(item=>({respondent_id:item.respondent_id,n:whole(item.n),mae:fmt(item.abs/item.n,2),naive:fmt(item.naive/item.n,2)}));
 return <><Notice tone="warning">Evaluasi perbandingan algoritma pada <strong>DATA SINTETIS / SIMULASI</strong>. Angka dibaca dari artefak terverifikasi hash (run {comparison.run_id}), bukan dihitung ulang pada filter aktif dan bukan bukti performa pada responden asli. Target belum disetujui dosen.</Notice>
 {(comparison.warnings||[]).map(w=><Notice key={w} tone="warning">{w}</Notice>)}
 <div className="metrics-overview"><div><span>Target regresi</span><b>Rerata SBP {comparison.horizon_days} hari berikutnya (mmHg)</b></div><div><span>Responden train / test</span><b>{whole(comparison.respondents_train.length)} / {whole(comparison.respondents_test.length)} ID</b></div><div><span>Window train / test</span><b>{whole(comparison.rows_training)} / {whole(comparison.rows_test)}</b></div><div><span>Periode</span><b>Cutoff training {comparison.cutoff}; test setelahnya</b></div><div><span>Sumber data</span><b>{comparison.dataset}</b></div><div><span>Pemisahan data</span><b>ID terpisah + batas waktu + target uji tidak overlap</b></div></div>
 <div className="page-grid two">
 <ChartCard title="RMSE: validasi vs test" sample={`${whole(rows[0].validation.n)} window validasi; ${whole(rows[0].test.n)} origin test`} description="RMSE dalam mmHg (lebih kecil lebih baik), memberi bobot lebih pada error besar. Validasi dipakai memilih model; test dilihat sekali setelah pemilihan dan tidak untuk memilih ulang."><ValidationVsTest comparison={comparison} metric="rmse"/></ChartCard>
 <ChartCard title="MAE: validasi vs test" sample={`${whole(rows[0].validation.n)} window validasi; ${whole(rows[0].test.n)} origin test`} description="MAE adalah rata-rata besar kesalahan absolut dalam mmHg. Ini bukan akurasi persen."><ValidationVsTest comparison={comparison} metric="mae"/></ChartCard>
 </div>
 <Card title="Tabel metrik perbandingan"><MiniTable rows={rows.map(row=>({model:row.model+(row.model===selected?' (terpilih)':''),kind:row.kind,vmae:nf(row.validation.mae),vrmse:nf(row.validation.rmse),vr2:nf(row.validation.r2),tmae:nf(row.test.mae),trmse:nf(row.test.rmse),tr2:nf(row.test.r2)}))} columns={[["model","Metode"],["kind","Jenis"],["vmae","MAE validasi (mmHg)"],["vrmse","RMSE validasi (mmHg)"],["vr2","R2 validasi"],["tmae","MAE test (mmHg)"],["trmse","RMSE test (mmHg)"],["tr2","R2 test"]]}/><Explainer>R2 membandingkan variasi yang dijelaskan terhadap prediksi rerata; dapat negatif dan bukan persentase akurasi. Model terpilih ditentukan aturan tetap: {comparison.selection.rule}. Mengalahkan baseline naif pada validasi: <b>{comparison.selection.beats_naive_on_validation?'ya':'tidak'}</b>.</Explainer></Card>
 <div className="page-grid two">
 <ChartCard title={`Aktual vs prediksi ${selected}`} sample={`${whole(predictions.length)} origin uji`} description="Titik dekat garis prediksi = aktual berarti error kecil. Sampel uji sangat kecil sehingga pola tidak stabil."><ActualVsPredicted model={comparison} field={key} label={selected}/></ChartCard>
 <ChartCard title={`Residual ${selected}`} sample={`${whole(predictions.length)} origin uji`} description="Residual = aktual - prediksi (mmHg). Positif berarti prediksi terlalu rendah."><ResidualPlot model={comparison} field={key}/></ChartCard>
 <ChartCard title="Distribusi error" sample={`${whole(predictions.length)} origin uji`} description="Histogram residual model terpilih. Dengan sampel kecil, bentuk distribusi tidak boleh ditafsirkan sebagai sifat model."><ResidualHistogram model={comparison} field={key}/></ChartCard>
 <Card title="Error per responden (test)"><MiniTable rows={byId} columns={[["respondent_id","ID"],["n","Origin uji"],["mae","MAE model terpilih (mmHg)"],["naive","MAE baseline naif (mmHg)"]]}/><Explainer>Analisis per kelompok memakai ID karena atribut lain terlalu sedikit pada test. Satu atau dua origin per ID tidak cukup untuk kesimpulan per kelompok.</Explainer></Card>
 </div>
 <Card title="Detail eksperimen dan keterbatasan"><p><b>Split:</b> {comparison.split}.</p><p><b>Run artefak:</b> {comparison.run_id}; seed {comparison.seed}; validasi {comparison.validation_folds} fold.</p><p><b>Fitur:</b> {(comparison.features||[]).join(', ')}.</p><p><b>Keterbatasan:</b> {comparison.limitation}</p><Explainer>Hasil tidak membuktikan generalisasi atau validitas klinis. Langkah lanjut menunggu persetujuan target oleh dosen dan validasi ekspor data aktual.</Explainer></Card></>;
}
export function Laporan({data,go}){
 if(!data||data.empty||data.kpis.sessions===0)return <Empty message={data?.message}/>;
 const k=data.kpis,q=data.filtered_quality;
 const pagi=data.session_stats.find(row=>row.session==='Pagi'),malam=data.session_stats.find(row=>row.session==='Malam');
 const first=data.trend.map(row=>row.date).sort()[0],last=data.trend.map(row=>row.date).sort().at(-1);
 const gap=pagi&&malam?malam.sbp-pagi.sbp:null;
 const findings=[
  [`${whole(k.respondents)} ID menyumbang ${whole(k.daily_records)} catatan harian`,`Cakupan ${first} sampai ${last}: ${whole(k.sessions)} sesi valid. Jumlah catatan berulang bukan jumlah individu independen.`],
  [`Rerata sesi ${fmt(k.mean_sbp,1)}/${fmt(k.mean_dbp,1)} mmHg`,`Rerata dihitung dari seluruh sesi valid, sehingga responden dengan lebih banyak sesi memiliki bobot pengamatan lebih besar. Ini bukan prevalensi atau diagnosis.`],
  [gap==null?'Perbandingan pagi-malam belum lengkap':`Selisih rerata Malam - Pagi ${gap>0?'+':''}${fmt(gap,2)} mmHg`,`Pagi n=${whole(pagi?.n)} sesi, Malam n=${whole(malam?.n)} sesi. Perbandingan ini tidak berpasangan per orang-hari dan tidak mengisolasi pengaruh waktu.`],
  [`${whole(q.incomplete_sessions)} sesi tidak lengkap tetap dicatat`,`${whole(q.missing_sleep_hours)} tidur, ${whole(q.missing_sitting)} duduk, dan ${whole(q.missing_smoke_count)} jumlah merokok kosong dari ${whole(q.daily_records)} catatan harian. Prioritaskan verifikasi sumber sebelum menafsirkan asosiasi.`],
  ['Keputusan kerja: periksa kelengkapan sebelum memperluas analisis','Telusuri periode, ID dan kategori dengan sampel kecil melalui filter. Dataset sintetis menguji alur teknis; temuan ini tidak menjadi rekomendasi kesehatan atau bukti penelitian aktual.']
 ];
 return <><div className="welcome"><div><span className="eyebrow">CERITA DATA PADA FILTER AKTIF</span><h2>Apa yang dapat disimpulkan, dan apa batasnya?</h2><p>Ringkasan diperbarui dari sumber yang sama dengan KPI dan grafik.</p></div></div>
 <div className="story-list">{findings.map(([title,description],index)=><article className="story" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{description}</p></div></article>)}</div>
 <ChartCard title={`SBP pada ${whole(k.sessions)} sesi valid selama ${whole(k.dates)} tanggal`} sample={`${whole(k.respondents)} ID aktif; ${first} sampai ${last}`} description="Garis menggambarkan rerata per tanggal-sesi. Perubahan komposisi responden dan missing dapat menjelaskan perubahan pola; data sintetis tidak mendukung inferensi populasi."><SessionLines rows={data.trend}/></ChartCard>
 <div className="data-actions"><button className="button primary" onClick={()=>go('Analisis Faktor Risiko')}>Periksa faktor gaya hidup <ArrowRight size={15}/></button><button className="button light" onClick={()=>go('Kelola Data')}>Periksa kualitas dan ekspor</button></div>
 <Notice>Keterbatasan: pengukuran berulang, ukuran kelompok tidak seimbang, data laporan mandiri, potensi faktor perancu, serta definisi tidur aktual dan target ML yang belum final. Hasil masih DATA SINTETIS / SIMULASI.</Notice></>;
}

export function KelolaData({meta,data,filters,reload}){
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
