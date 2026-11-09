import React,{useEffect,useRef,useState} from 'react';
import {Activity,ArrowRight,BookOpen,Database,Download,FileCheck2,HeartPulse,Target,UsersRound,CalendarDays} from 'lucide-react';
import {Card,Notice,MiniTable,Empty,Loading} from '../components/Common';
import {SessionLines,SessionBox,SessionHeatmap,NumericScatter,StressBox,CategoryBars,PieCategories,WorkTreemap,SmallMultiples,ModelComparison,ActualVsPredicted,ResidualPlot,CountBars,Histogram} from '../components/Visuals';
import {api,fmt,whole,queryString,download} from '../lib/api';

function Explainer({children}){return <p className="chart-explainer">{children}</p>}
function ChartCard({title,sample,description,children}){return <Card title={title} className="analysis-card">{sample&&<p className="sample-note">{sample}</p>}{children}<Explainer>{description}</Explainer></Card>}
const dailySample=rows=>`${whole(rows.length)} ID-tanggal dari ${whole(new Set(rows.map(row=>row.respondent_id)).size)} ID`;
const categorySample=rows=>`${whole((rows||[]).reduce((sum,row)=>sum+row.n,0))} catatan harian valid; jumlah ID tiap kategori pada tooltip`;
function KPI({icon:Icon,label,value,unit,desc,previous,current}){
 const delta=previous!=null&&Number.isFinite(current)?current-previous:null;
 return <div className="kpi kpi-biru"><div className="kpi-ico"><Icon size={22}/></div><div className="kpi-content"><div className="kpi-label" title={desc}>{label}</div><div className="kpi-value">{value}<small>{unit}</small></div><div className="kpi-sub">{desc}</div>{previous!=null&&<span className="kpi-compare">Sebelumnya {fmt(previous,unit?1:0)}{unit} | {delta>0?'+':''}{fmt(delta,unit?1:0)}{unit}</span>}</div></div>;
}
export function QualitySummary({data}){
 const q=data?.filtered_quality;if(!q)return <Notice>Kualitas pilihan belum dapat dibaca.</Notice>;
 const completeness=q.session_records?100*q.valid_sessions/q.session_records:null;
 return <Card title="Kualitas data pada filter aktif"><div className="quality-grid">{[
  ['Kelengkapan sesi',completeness==null?null:fmt(completeness,1)+'%'],['Sesi tidak lengkap',whole(q.incomplete_sessions)],['Tidur kosong',whole(q.missing_sleep_hours)],['Duduk kosong',whole(q.missing_sitting)],['Jumlah merokok kosong',whole(q.missing_smoke_count)]
 ].map(([label,value])=><div key={label}><span>{label}</span><b>{value??'Tidak tersedia'}</b></div>)}</div><Explainer>Kelengkapan sesi = sesi dengan SBP dan DBP valid / seluruh sesi tercatat. Missing perilaku dihitung per ID-tanggal, tidak diisi nol. Baris harian valid berarti diterima ETL, bukan semua kolom lengkap.</Explainer></Card>;
}
export function Dashboard({data,go,onFilter}){
 if(!data||data.empty)return <Empty message={data?.message}/>;
 const k=data.kpis,prev=data.comparison?.has_data?data.comparison:null;
 return <>
 <div className="welcome"><div><span className="eyebrow">DASHBOARD V1 | CP3 - MINGGU 8</span><h2>Bagaimana cakupan dan pola pengukuran pada periode ini?</h2><p>Ringkasan pengamatan, bukan jumlah pasien atau diagnosis. SBP = sistolik; DBP = diastolik.</p></div><button className="button primary" onClick={()=>go('Tren Tekanan Darah')}>Lihat tren <ArrowRight size={15}/></button></div>
 <div className="kpi-grid"><KPI icon={UsersRound} label="Responden aktif" value={whole(k.respondents)} current={k.respondents} previous={prev?.active} desc="ID unik dengan sedikitnya satu sesi valid"/><KPI icon={CalendarDays} label="Catatan harian valid" value={whole(k.daily_records)} current={k.daily_records} previous={prev?.daily} desc="ID-tanggal diterima ETL; missing tetap dipertahankan"/><KPI icon={Activity} label="Sesi valid" value={whole(k.sessions)} current={k.sessions} previous={prev?.sessions} desc="Memiliki rerata SBP dan DBP; pagi/malam terpisah"/><KPI icon={HeartPulse} label="Rata-rata SBP" value={fmt(k.mean_sbp,1)} current={k.mean_sbp} previous={prev?.sbp} unit=" mmHg" desc={`Rerata ${whole(k.sessions)} sesi valid, bukan rerata per orang`}/></div>
 <Notice>{data.comparison?data.comparison.has_data?`Pembanding: ${data.comparison.period}, periode sebelumnya dengan panjang yang sama dan filter non-tanggal yang sama. Selisih ditampilkan sebagai perubahan deskriptif, bukan indikator baik/buruk.`:`Belum ada data pembanding pada periode ${data.comparison.period}.`:'Pilih tanggal mulai dan sampai untuk membandingkan dengan periode sebelumnya yang sama panjang.'}</Notice>
 <QualitySummary data={data}/>
 <p className="interaction-hint">Klik titik tren atau sel heatmap untuk memfilter tanggal dan sesi pada seluruh halaman analitik. Pilihan juga tersedia pada filter global.</p>
 <div className="page-grid two">
 <ChartCard title="Tren SBP: pagi dan malam" sample={`${whole(k.sessions)} sesi valid`} description="Rerata tiap tanggal-sesi; tooltip menunjukkan n sesi. Pergeseran garis dapat dipengaruhi komposisi responden, bukan perubahan individu yang pasti."><SessionLines rows={data.trend} onSelect={onFilter}/></ChartCard>
 <ChartCard title="Tren DBP: pagi dan malam" sample={`${whole(k.sessions)} sesi valid`} description="DBP dalam mmHg. Bandingkan pada tanggal yang sama; selisih agregat tidak membuktikan pengaruh waktu pengukuran."><SessionLines rows={data.trend} field="dbp" onSelect={onFilter}/></ChartCard>
 <ChartCard title="Distribusi SBP menurut sesi" sample={`${whole(k.sessions)} sesi valid`} description="Garis tengah kotak menunjukkan median; kotak menunjukkan kuartil. Titik ekstrem dipertahankan dan bukan diagnosis."><SessionBox rows={data.session_box}/></ChartCard>
 <ChartCard title="Heatmap SBP per tanggal dan sesi" sample={`${whole(k.dates)} tanggal dengan catatan harian`} description="Warna lebih pekat menunjukkan rerata SBP lebih tinggi, bukan tingkat diagnosis. Sel kosong berarti nilai tidak tersedia."><SessionHeatmap rows={data.heatmap} onSelect={onFilter}/></ChartCard>
 </div></>;
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
 if(!data||data.empty)return <Empty message={data?.message}/>;
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
 <Notice>Dua pembacaan dirata-ratakan per sesi sesuai CP2. Jika hanya satu pembacaan valid tersedia, rerata sesi memakai pembacaan itu. Waktu pengamatan menggunakan tanggal formulir, bukan timestamp pengiriman.</Notice>
 {valid.length?<div className="page-grid two">
 <ChartCard title="Tren SBP pagi dan malam" sample={`${whole(valid.length)} sesi valid`} description="Klik titik untuk memilih tanggal-sesi. Gunakan reset filter untuk kembali ke seluruh periode."><SessionLines rows={trend} onSelect={onFilter}/></ChartCard>
 <ChartCard title="Tren DBP pagi dan malam" sample={`${whole(valid.length)} sesi valid`} description="DBP dalam mmHg, dihitung dari sesi valid pada filter yang sama dengan tabel detail."><SessionLines rows={trend} field="dbp" onSelect={onFilter}/></ChartCard>
 <ChartCard title="Distribusi SBP sesi" sample={`${whole(valid.length)} sesi valid`} description="Median dan kuartil merangkum penyebaran. Pencilan tetap dipertahankan untuk ditelusuri pada tabel."><SessionBox rows={valid}/></ChartCard>
 <ChartCard title="Heatmap SBP menurut waktu" sample={`${whole(valid.length)} sesi valid`} description="Warna = rerata SBP, tooltip = jumlah sesi. Klik sel untuk memilih tanggal dan Pagi/Malam; sel missing tidak diberi nol."><SessionHeatmap rows={trend} onSelect={onFilter}/></ChartCard>
 </div>:<Empty message={data.message}/>}
 <Card title="Detail pembacaan tekanan darah"><Explainer>Seluruh tekanan darah dalam mmHg. Dua pembacaan dan jumlah bacaan valid ditampilkan; satu baris = ID-tanggal-sesi. Missing ditampilkan sebagai tanda kosong.</Explainer><MiniTable rows={rows.map(row=>({...row,sbp_mean:fmt(row.sbp_mean,1),dbp_mean:fmt(row.dbp_mean,1),valid_label:row.is_valid?'Valid':'Tidak lengkap'}))} columns={[["respondent_id","ID"],["date","Tanggal"],["session","Sesi"],["measured_at","Jam"],["sbp1","SBP 1"],["dbp1","DBP 1"],["sbp2","SBP 2"],["dbp2","DBP 2"],["sbp_mean","Rerata SBP"],["dbp_mean","Rerata DBP"],["valid_sbp_count","n SBP"],["valid_dbp_count","n DBP"],["valid_label","Status"]]}/></Card></>;
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
  try{const response=await api('/model/predict-baseline?respondent_id='+encodeURIComponent(rid),{signal:controller.signal});if(serial===sequence.current)setResult(response)}
  catch(err){if(serial===sequence.current&&err.name!=='AbortError')setError(err.message)}
  finally{if(serial===sequence.current)setLoading(false)}
 }
 return <><Notice tone="warning"><strong>Baseline eksperimen - DATA SINTETIS / SIMULASI.</strong> Memperkirakan rerata sistolik tujuh hari berikutnya, bukan klasifikasi hipertensi atau diagnosis. Target akhir masih memerlukan persetujuan dosen.</Notice>
 {modelLoading&&<Loading/>}
 {!modelLoading&&!model?.available&&<Notice tone="warning">{model?.message||'Artefak baseline belum tersedia. Tidak ada perkiraan contoh yang diisi otomatis.'}</Notice>}
 <div className="page-grid two"><Card title="Input: riwayat responden simulasi" icon={Target}><form className="predict-form" onSubmit={submit}><label className="field"><span>ID responden simulasi</span><select aria-label="ID prediksi baseline" value={rid} onChange={event=>choose(event.target.value)}>{(meta?.respondent_ids||[]).map(id=><option key={id} value={id}>{id}</option>)}</select></label>
 <p className="muted">API memerlukan tujuh hari kalender berturut-turut pada akhir riwayat ID. Anda memilih riwayat yang sudah ada di PostgreSQL; ini belum form fitur baru untuk model final.</p>
 <button className="button primary" type="submit" disabled={loading||modelLoading||!rid||!model?.available}>{loading?'Menghitung...':'Hitung perkiraan baseline'}</button></form>
 {error&&<Notice tone="error">{error}. Periksa kelengkapan riwayat ID, lalu coba lagi.</Notice>}
 <div aria-live="polite">{result&&<div className="prediction-result"><span>Output: estimasi rerata SBP tujuh hari berikutnya</span><strong className="prediction-number">{fmt(result.prediction_mmHg,2)} mmHg</strong><small>ID {result.respondent_id} | Akhir riwayat {result.last_date}</small>{result.forecast_start&&<small>Rentang estimasi {result.forecast_start} sampai {result.forecast_end}</small>}<p>Metode: {result.baseline}. Tidak disertai interval keyakinan dan tidak digunakan untuk keputusan medis.</p></div>}</div></Card>
 <Card title="Cara membaca baseline" icon={BookOpen}><div className="guide-steps"><div><b>1</b><span>Pilih ID dengan sedikitnya tujuh hari berurutan. Riwayat terakhir ditentukan oleh tanggal data, bukan tanggal komputer.</span></div><div><b>2</b><span>Endpoint baseline lama memakai sesi dengan SBP tersedia, lalu menghitung rerata SBP harian.</span></div><div><b>3</b><span>Rerata tujuh hari terakhir menjadi estimasi rerata tujuh hari mendatang. Hari yang belum diukur tidak dibuatkan data.</span></div></div>
 <Explainer>Linear Regression hanya pembanding pada eksperimen tersimpan. Algoritma, kriteria baseline dan artefak ML dipertahankan; tabel analitik memakai syarat SBP dan DBP valid yang dijelaskan pada dashboard.</Explainer></Card></div></>;
}
export function Evaluasi({model,modelLoading}){
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
export function Laporan({data,go}){
 if(!data||data.empty)return <Empty message={data?.message}/>;
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
 <Card title="Unduh hasil filter" icon={Download}><div className="export-row">{[['participants','Profil'],['daily','Catatan harian'],['sessions','Sesi tensi']].map(([kind,label])=><button key={kind} type="button" className="button light" disabled={!!busy||!data} onClick={()=>exportData(kind)}><Download size={14}/>{busy===kind?'Mengunduh...':label}</button>)}</div>{error&&<Notice tone="error">{error}</Notice>}</Card>
 <Card title="Petunjuk validasi ETL"><p>Jalankan dari root project pada lingkungan Python yang benar. Perintah ini hanya validasi, tanpa mengubah database:</p><pre className="etl-command"><code>python -m etl.import_data --synthetic --dry-run --summary</code></pre><ol><li>Validasi dua formulir melalui ETL dry-run.</li><li>Periksa kualitas dan target database, lalu minta persetujuan pengelola.</li><li>Terapkan ETL manual dengan prasyarat hash target yang disetujui.</li><li>Klik Muat ulang data untuk membaca hasil terbaru.</li></ol><p>Dataset aktual memakai kontrak yang sama. Akses publik ke data aktual tetap dibatasi sampai kontrol akses tersedia.</p><button className="button light" type="button" onClick={reload}>Baca ulang warehouse</button></Card>
 </>;
}
