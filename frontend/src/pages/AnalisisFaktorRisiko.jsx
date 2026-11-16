import React from 'react';
import {Card,Notice,MiniTable,Empty} from '../components/Common';
import {SessionBox,NumericScatter,StressBox,CategoryBars,PieCategories,WorkTreemap,SmallMultiples} from '../components/Visuals';
import {fmt,whole} from '../lib/api';
import {ChartCard,Explainer} from '../components/page-shared/Analysis';

const dailySample=rows=>`${whole(rows.length)} ID-tanggal dari ${whole(new Set(rows.map(row=>row.respondent_id)).size)} ID`;
const categorySample=rows=>`${whole((rows||[]).reduce((sum,row)=>sum+row.n,0))} catatan harian valid; jumlah ID tiap kategori pada tooltip`;

export default function FaktorRisiko({data,onFilter}){
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
