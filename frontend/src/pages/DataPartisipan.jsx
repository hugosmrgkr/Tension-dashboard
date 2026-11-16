import React,{useState} from 'react';
import {Card,Notice,MiniTable,Empty} from '../components/Common';
import {PieCategories,CountBars,Histogram} from '../components/Visuals';
import {fmt,whole} from '../lib/api';
import {ChartCard,Explainer} from '../components/page-shared/Analysis';

export default function DataPartisipan({data,onFilter}){
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
