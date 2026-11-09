"""CP2 EDA and report rendering; uses exactly the prepared warehouse grain."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from .survey_schema import PROFILE_FIELDS, DAILY_FIELDS
from .pipeline import EXPECTED_PROFILE_HEADERS, EXPECTED_DAILY_HEADERS


def markdown_table(headers, rows):
    def cell(value):
        return str(value if value is not None else '—').replace('|','\\|').replace('\n','<br>')
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(cell(v) for v in row)+' |' for row in rows])


def dictionary_markdown():
    parts=['# Data dictionary lengkap — CP2',
           '**SIMULASI.** Kontrak fixture terdiri dari 24 kolom Form Awal dan 28 kolom Form Harian. '
           'Header harus cocok setelah normalisasi BOM/spasi/kapital, dengan urutan yang sama. '
           'Penambahan atau pemindahan kolom memerlukan pembaruan kontrak; tidak dipetakan secara tebakan.',
           'Relasi: satu `respondent_id` pada profil → banyak ID-tanggal pada harian → dua sesi Pagi/Malam. '
           'Setiap sesi menyimpan dua pembacaan sistolik dan diastolik. Usia/BMI berasal dari profil; '
           'perilaku dan stres berasal dari hari pengamatan.',
           'Missing kosong/NaN/None/NaT tetap NA; tidak diimputasi nol. ID atau tanggal tidak valid, '
           'ID tanpa profil, serta duplikasi berikutnya dikarantina pada tingkat baris. '
           'Sel non-kunci invalid menjadi NA dengan issue. Timestamp hanya metadata audit; nama dikeluarkan.']
    for title, headers, specs in [('Form Awal',EXPECTED_PROFILE_HEADERS,PROFILE_FIELDS),('Form Harian',EXPECTED_DAILY_HEADERS,DAILY_FIELDS)]:
        rows=[]
        for index,(name,spec) in enumerate(zip(headers,specs),1):
            categories='; '.join(spec['categories']) or 'Teks sumber / numerik sesuai tipe'
            rule=(f"Rentang teknis {spec['bounds'][0]}–{spec['bounds'][1]}. " if spec['bounds'] else '')
            rule+=(f"Maksimum {spec['max_length']} karakter. " if spec['max_length'] else '')
            transform='Normalisasi spasi/kapital ke label enum' if spec['kind'] in ('category','open_category') else 'Parse numerik; terima sufiks hanya sesuai satuan' if spec['kind'] in ('number','integer') else 'Parse sesuai definisi tipe'
            missing='Tidak dimuat (identitas)' if spec['kind']=='excluded' else 'Karantina baris bila kosong/invalid' if spec['kind'] in ('id','date') else 'NA; catat bila tidak valid'
            rows.append([index,name,spec['technical'],title,spec['kind'],spec['unit'],categories,missing,rule+spec['note'],transform])
        parts.extend(['## '+title,markdown_table(['No.','Nama asli','Nama teknis','Sumber','Tipe','Satuan','Kategori','Missing','Validasi / catatan','Transformasi'],rows)])
    parts.extend(['## Kolom turunan dan penyimpanan',
        markdown_table(['Kolom','Rumus / asal','Grain / perlakuan'],[
            ['bmi','weight_kg / (height_cm/100)^2, dibulatkan 3 desimal','Profil; NA jika tinggi/berat tidak valid'],
            ['conditions_json','11 kunci riwayat pada Form Awal kolom 10–20','Profil; setiap jawaban kosong tetap null'],
            ['sbp_mean / dbp_mean','Rata-rata pembacaan tersedia yang lolos validasi, terpisah per variabel','ID × tanggal × sesi; semua pembacaan hilang → NA'],
            ['valid_sbp_count / valid_dbp_count','Jumlah pembacaan valid 0–2','Sesi valid untuk analitik bila kedua hitungan minimal 1'],
            ['session','Pagi/Malam dari pasangan kolom sumber','Bukan pertanyaan baru; pemisahan struktur wide → long'],
            ['year/month/day','Komponen tanggal pengamatan','Dimensi tanggal'],
            ['ID surrogate / FK','Dibuat database, bukan ID responden baru','PK teknis, berbeda dari respondent_id sumber'],
            ['future_7d_mean_sbp','Usulan target tahap modelling','Di luar CP2; tidak dibuat/diubah oleh pekerjaan ini']]),
        '## Aturan format dan kategori',
        '- Integer menerima angka bulat saja; `3 hari`, `45 menit`, `21 tahun`, `165 cm`, `60,5 kg` hanya diterima pada kolom dengan satuan yang sesuai. `3.5 hari` tidak dibulatkan diam-diam.\n'
        '- Tanggal menerima ISO `YYYY-MM-DD`/datetime ISO atau `DD/MM/YYYY` eksplisit; waktu menerima `HH:MM[:SS]`. Nomor serial Excel dan teks tanggal ambigu ditahan, bukan ditebak.\n'
        '- Kategori tertutup yang tidak dikenal menjadi NA dengan issue. Kategori aktivitas/konteks terbuka dipertahankan dengan flag review. Pekerjaan, pendidikan, provinsi dan kota bukan enum geografis yang telah diverifikasi.\n'
        '- Multi-pilihan aktivitas umum tidak dipisahkan dengan koma: label pilihan juga mengandung koma.\n'
        '- Mapping khusus fixture sintetis: `4�7 jam`/`4-7 jam` → `4–7 jam`; `8�10 jam`/`8-10 jam` → `8–10 jam`. Raw tidak diubah. Mapping karakter rusak ini tidak diterapkan otomatis pada data aktual.\n'
        '- Tidur sintetis `06:30` → 6,5 jam. Pecahan 0<x<1 ditandai ambigu (dapat berupa pecahan hari Excel), tidak dikali 24 atau dianggap jam otomatis. Data aktual seluruhnya menunggu keputusan semantik.\n'
        '- Rentang BP 60–260 sistolik, 35–170 diastolik adalah pagar teknis proyek, bukan pedoman diagnosis. Nilai di luar pagar menjadi NA dengan alasan; sumber mentah tetap ada. IQR dan SBP≤DBP hanya flag review.\n'
        '- Tidak ada kriteria inklusi usia final yang dipaksakan. Usia teknis 0–120; kelayakan responden ditentukan terpisah bersama dosen.\n'
        '- Semua perubahan kategori/satuan dapat ditelusuri lewat laporan normalisasi dan hash sumber. Tidak ada identitas langsung dalam keluaran analitik.'
    ])
    return '\n\n'.join(parts)+'\n'


def analyze(profiles,days,sessions,quality):
    p=pd.DataFrame(profiles).drop(columns=['conditions_json'])
    d=pd.DataFrame(days)
    s=pd.DataFrame(sessions)
    valid=s.dropna(subset=['sbp_mean','dbp_mean']).copy()
    daily_bp=valid.groupby(['respondent_id','date'],as_index=False)[['sbp_mean','dbp_mean']].mean()
    daily=d.merge(daily_bp,on=['respondent_id','date'],how='left').merge(
        p[['respondent_id','age','bmi']],on='respondent_id',how='left',validate='many_to_one')
    trend=valid.groupby(['date','session'],as_index=False)[['sbp_mean','dbp_mean']].mean()
    paired=valid.pivot(index=['respondent_id','date'],columns='session',values='sbp_mean').reindex(columns=['Pagi','Malam']).dropna()
    correlation=daily[['age','bmi','sleep_hours','activity_minutes','heavy_minutes','stress','sbp_mean','dbp_mean']].corr()
    demo=dict(respondents=len(p),days=len(d),sessions=len(s),valid_sessions=len(valid),dates=d.date.nunique(),
              provinces=p.province.nunique(),cities=p.city.nunique(),mean_age=float(p.age.mean()),
              min_age=int(p.age.min()),max_age=int(p.age.max()),gender=p.gender.value_counts().to_dict())
    session_summary=valid.groupby('session')[['sbp_mean','dbp_mean']].agg(['count','mean','std','min','max'])
    first_date,last_date=trend.date.min(),trend.date.max()
    first_mean=float(valid.loc[valid.date==first_date,'sbp_mean'].mean())
    last_mean=float(valid.loc[valid.date==last_date,'sbp_mean'].mean())
    r_activity=correlation.loc['activity_minutes','sbp_mean']
    r_sleep=correlation.loc['sleep_hours','sbp_mean']
    delta=float((paired['Malam']-paired['Pagi']).mean()) if len(paired) else None
    paired_text=f"{len(paired)} pasangan ID-tanggal lengkap; rerata selisih Malam−Pagi {delta:.3f} mmHg" if delta is not None else 'Tidak ada pasangan lengkap untuk membandingkan sesi'
    findings=[
        dict(title='Cakupan profil dan variasi demografi',figure='01_profile_age.png',text=
             f"SIMULASI: {len(p)} ID, {d.date.nunique()} tanggal, {len(d)} catatan harian dan {len(valid)} sesi valid. Usia {demo['min_age']}–{demo['max_age']} tahun, rerata {demo['mean_age']:.2f}; {demo['provinces']} provinsi dan {demo['cities']} kabupaten/kota. Jumlah catatan berulang tidak sama dengan jumlah orang."),
        dict(title='Perbandingan pagi–malam berpasangan',figure='05_session_comparison.png',text=
             f"SIMULASI: {paired_text}. Perbandingan memasangkan orang dan tanggal yang sama; ini statistik deskriptif, bukan efek kausal waktu."),
        dict(title='Perubahan rerata harian selama periode simulasi',figure='06_daily_trend.png',text=
             f"SIMULASI: rerata sistolik sesi pada {first_date} adalah {first_mean:.3f} mmHg dan pada {last_date} {last_mean:.3f} mmHg (selisih {last_mean-first_mean:+.3f} mmHg). Dua titik ini bukan bukti tren populasi atau perubahan klinis."),
        dict(title='Hubungan gaya hidup pada grain harian',figure='08_numeric_correlation.png',text=
             f"SIMULASI: korelasi Pearson aktivitas menit–SBP harian {r_activity:.3f}; tidur–SBP harian {r_sleep:.3f}. Perhitungan satu baris per ID-tanggal, bukan menduplikasi perilaku ke dua sesi. Catatan dari orang yang sama saling berkaitan; tidak digunakan untuk uji kausal atau signifikansi populasi."),
        dict(title='Missing tetap terlihat setelah cleaning',figure='09_missing_before_after.png',text=
             f"SIMULASI: tidur kosong {quality['missing_sleep']}/{len(d)} ({100*quality['missing_sleep']/len(d):.3f}%), duduk kosong {quality['missing_sitting']}/{len(d)} ({100*quality['missing_sitting']/len(d):.3f}%). Jumlah merokok NA {int(d.smoke_count.isna().sum())}/{len(d)}; status merokok tidak dipakai untuk mengisi nol. {quality['pressure_anomalies']['flagged_sessions']} sesi diberi flag IQR; tidak ada sesi yang dihapus hanya karena flag statistik.")
    ]
    summary=dict(label='SIMULASI — BUKAN DATA PENELITIAN AKTUAL',demographics=demo,
                 session_summary=json.loads(session_summary.reset_index().to_json(orient='split')),
                 paired_sbp_difference=delta,paired_rows=len(paired),findings=findings,
                 stress_summary=json.loads(daily.groupby('stress').sbp_mean.agg(['count','mean','std']).reset_index().to_json(orient='records')),
                 correlation=json.loads(correlation.to_json()),
                 completeness=dict(sleep_missing=quality['missing_sleep'],sitting_missing=quality['missing_sitting']))
    return dict(profiles=p,daily=daily,sessions=s,valid_sessions=valid,trend=trend,correlation=correlation,summary=summary)


def make_figures(eda, quality):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.rcParams.update({'figure.dpi':110,'axes.titlesize':10,'axes.labelsize':9})
    p,d,s,tr=eda['profiles'],eda['daily'],eda['valid_sessions'],eda['trend']
    figures={}
    fig,ax=plt.subplots(figsize=(7,4)); ax.hist(p.age,bins=8,color='#2f6fe0',edgecolor='white')
    ax.set(title='SIMULASI — Distribusi usia profil',xlabel='Usia (tahun)',ylabel='Jumlah responden (orang)'); figures['01_profile_age.png']=fig
    fig,ax=plt.subplots(figsize=(7,4)); p.gender.value_counts().plot.bar(ax=ax,color=['#2f6fe0','#20a99c'],rot=0)
    ax.set(title='SIMULASI — Distribusi jenis kelamin',xlabel='Kategori jenis kelamin',ylabel='Jumlah responden (orang)'); figures['02_profile_gender.png']=fig
    fig,ax=plt.subplots(figsize=(8,6)); p.city.value_counts().sort_values().plot.barh(ax=ax,color='#2f6fe0')
    ax.set(title='SIMULASI — Cakupan kabupaten/kota',xlabel='Jumlah responden (orang)',ylabel='Kabupaten/kota'); figures['03_profile_location.png']=fig
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,col,label in zip(axes,['sbp_mean','dbp_mean'],['Sistolik','Diastolik']):
        ax.hist(s[col],bins=20,color='#2f6fe0',edgecolor='white'); ax.set(title=f'SIMULASI — Distribusi {label}',xlabel=label+' rerata sesi (mmHg)',ylabel='Jumlah sesi valid')
    figures['04_pressure_distribution.png']=fig
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,col,label in zip(axes,['sbp_mean','dbp_mean'],['Sistolik','Diastolik']):
        ax.boxplot([s.loc[s.session==name,col] for name in ['Pagi','Malam']],tick_labels=['Pagi','Malam'])
        ax.set(title=f'SIMULASI — {label} pagi dan malam',xlabel='Sesi pengukuran',ylabel=label+' (mmHg)')
    figures['05_session_comparison.png']=fig
    fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
    for ax,col,label in zip(axes,['sbp_mean','dbp_mean'],['Sistolik','Diastolik']):
        for name in ['Pagi','Malam']:
            a=tr[tr.session==name]; ax.plot(pd.to_datetime(a.date),a[col],label=name)
        ax.set(title=f'SIMULASI — Tren rerata {label.lower()}',ylabel=label+' (mmHg)'); ax.legend()
    axes[-1].set_xlabel('Tanggal pengamatan'); axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    figures['06_daily_trend.png']=fig
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,col,label in zip(axes[:2],['sleep_hours','activity_minutes'],['Durasi tidur (jam, asumsi sintetis)','Aktivitas fisik (menit/hari)']):
        a=d.dropna(subset=[col,'sbp_mean']); ax.scatter(a[col],a.sbp_mean,s=10,alpha=.45)
        ax.set(title='SIMULASI — Hubungan deskriptif',xlabel=label,ylabel='SBP harian (mmHg)')
    groups=[x for x in [1,2,3,4,5] if len(d.loc[d.stress==x,'sbp_mean'].dropna())]
    axes[2].boxplot([d.loc[d.stress==x,'sbp_mean'].dropna() for x in groups],tick_labels=[str(x) for x in groups])
    axes[2].set(title='SIMULASI — Stres dan sistolik',xlabel='Stres (skor 1–5)',ylabel='SBP harian (mmHg)')
    figures['07_lifestyle.png']=fig
    fig,ax=plt.subplots(figsize=(8,7)); corr=eda['correlation']; im=ax.imshow(corr,vmin=-1,vmax=1,cmap='coolwarm')
    ax.set_xticks(range(len(corr)),corr.columns,rotation=60,ha='right'); ax.set_yticks(range(len(corr)),corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            value=corr.iloc[i,j]; ax.text(j,i,'NA' if pd.isna(value) else f'{value:.2f}',ha='center',va='center',fontsize=8)
    ax.set(title='SIMULASI — Pearson pada catatan harian berulang',xlabel='Variabel numerik (satuan lihat dictionary)',ylabel='Variabel numerik')
    fig.colorbar(im,ax=ax,label='Koefisien Pearson (−1 sampai 1)'); figures['08_numeric_correlation.png']=fig
    before=pd.DataFrame(quality['before']); after=pd.DataFrame(quality['after'])
    a=before[before.policy=='analytic'].merge(after[['source','field','missing_percent']],on=['source','field'],suffixes=('_before','_after'))
    a=a[(a.missing_percent_before>0)|(a.missing_percent_after>0)]
    fig,ax=plt.subplots(figsize=(9,4)); x=np.arange(len(a)); ax.bar(x-.18,a.missing_percent_before,.36,label='Raw'); ax.bar(x+.18,a.missing_percent_after,.36,label='Clean')
    ax.set_xticks(x,a.field,rotation=25,ha='right'); ax.set(title='SIMULASI — Missing sebelum/sesudah',xlabel='Kolom analitik',ylabel='Missing (%)',ylim=(0,105)); ax.legend()
    figures['09_missing_before_after.png']=fig
    anomaly=quality['pressure_anomalies']['summaries']; fig,ax=plt.subplots(figsize=(8,4))
    ax.bar([r['session']+' '+r['field'] for r in anomaly],[r['flagged'] for r in anomaly])
    ax.set(title='SIMULASI — Flag pencilan 1,5 IQR (tidak dihapus)',xlabel='Sesi dan variabel tekanan darah',ylabel='Jumlah nilai rerata sesi yang ditandai'); figures['10_pressure_anomalies.png']=fig
    for fig in figures.values(): fig.tight_layout()
    return figures


def quality_markdown(quality, manifest):
    q=quality
    sections=['# Laporan kualitas data CP2 — SIMULASI',
              'Hasil dihitung ulang dari dua CSV yang hash SHA-256-nya dicatat pada `reports/cp2/source_manifest.json`. '
              'Data sintetis tidak memenuhi bukti data primer. Tidak ada data mentah ditimpa, nama disalin, atau missing diimputasi nol.',
              '## Sumber dan hasil baris',
              markdown_table(['Sumber','Raw','Diterima / turunan','Dikarantina / tidak lengkap'],[
                  ['Profil',q['raw_profiles'],q['accepted_profiles'],q['rejected_profiles']],
                  ['Harian',q['raw_daily'],q['accepted_daily'],q['rejected_daily']],
                  ['Sesi','2 × harian diterima',q['row_outcomes']['sessions']['derived'],q['row_outcomes']['sessions']['incomplete']]]),
              'Karantina berupa nomor baris sumber dan alasan pada JSON/CSV. Baris pertama ID atau ID-tanggal dipertahankan; '
              'kemunculan berikutnya tidak menimpa data pertama. Semua sumber tetap tersedia untuk peninjauan koreksi. '
              'Kesalahan skema membatalkan seluruh batch sebelum load.',
              '## Completeness dan validity sebelum–sesudah',
              'Persentase menggunakan jumlah baris sumber/diterima masing-masing tabel. Missing dihitung terpisah dari invalid. '
              'Invalid menjadi NA berarti validity nilai teramati dapat meningkat sambil completeness menurun; ini bukan imputasi. '
              'Nama dikeluarkan, bukan dinilai sebagai missing baru. Tabel sesi memiliki grain berbeda sehingga tidak dibandingkan sebagai 28 kolom raw.',
              markdown_table(['Sumber','Kolom teknis','Raw n','Raw NA (%)','Raw invalid','Clean n','Clean NA (%)','Clean invalid'],
                 [[b['source'],b['field'],b['rows'],b['missing_percent'],b['invalid'],a['rows'],a['missing_percent'],a['invalid']]
                  for b,a in zip(q['before'],q['after'])]),
              '## Consistency dan uniqueness',
              markdown_table(['Pemeriksaan','Sebelum','Sesudah'],[
                  ['Kelebihan ID profil duplikat',q['uniqueness']['profile_duplicate_excess'],q['uniqueness']['clean_profile_duplicate_excess']],
                  ['Kelebihan pasangan ID-tanggal',q['uniqueness']['daily_duplicate_excess'],q['uniqueness']['clean_daily_duplicate_excess']],
                  ['Harian tanpa profil diterima',q['consistency']['unmatched_daily_rows'],q['consistency']['clean_unmatched_daily_rows']]]),
              f"Satuan clean: {q['consistency']['units']}. Profil aktivitas mingguan memakai parser `hari` yang sesuai satuan, tidak lagi kehilangan seluruh nilai.",
              '## Transformasi yang tercatat',
              markdown_table(['Kolom','Jumlah sel berubah representasi / normalisasi'],sorted(q['normalizations_by_field'].items())),
              'Perubahan representasi termasuk parse tanggal/waktu, angka bersatuan dan label stres. Alias kategori duduk dengan karakter rusak '
              'hanya dipetakan bila ditemukan pada simulasi, sebagaimana dictionary; label valid tetap dipertahankan. Data aktual tidak diperbaiki dengan tebakan.',
              '## Anomali tekanan darah',
              markdown_table(['Sesi','Variabel','n','Q1','Q3','Batas bawah IQR','Batas atas IQR','Ditandai'],
                  [[r[k] for k in ['session','field','n','q1','q3','lower','upper','flagged']] for r in q['pressure_anomalies']['summaries']]),
              f"{q['pressure_anomalies']['flagged_sessions']} sesi memiliki sedikitnya satu flag IQR; "
              f"{q['invalid_bp_count']} sel BP invalid. IQR dan SBP≤DBP tidak otomatis menghapus sesi. "
              'Pagar numerik teknis, nilai invalid, dan alasan dapat ditelusuri ke baris sumber. Batas tersebut bukan kriteria diagnosis.',
              '## Issue dan keputusan',
              markdown_table(['Kode','Jumlah'],sorted(q['issue_counts'].items())) if q['issue_counts'] else 'Tidak ditemukan issue tipe/rentang/konsistensi pada fixture ini; missing yang disengaja tetap dilaporkan.',
              'Tanggal mencurigakan: '+str(len(q['suspicious_dates']))+'. Rincian lengkap ada di `reports/cp2/quality.json` dan `issues.csv`.',
              '## Batas kesiapan',
              'Laporan ini membuktikan audit teknis fixture, bukan kelayakan penelitian aktual. Masih perlu keputusan dosen tentang '
              'semantik tidur, kriteria responden, minimum catatan/responden, izin data, serta aturan peninjauan nilai ekstrem. '
              'Registry wilayah dan pilihan lain di kuesioner aktual perlu diverifikasi sebelum kontrak diperluas.']
    return '\n\n'.join(sections)+'\n'


def findings_markdown(eda):
    parts=['# Lima temuan EDA CP2 — SIMULASI',
           'Seluruh angka dihitung dari hasil ETL dua CSV sintetis. Tidak digunakan untuk prevalensi, diagnosis, '
           'kesimpulan sebab-akibat atau klaim performa model. Lihat notebook `02_eda_data_readiness.ipynb` dan `reports/cp2/eda_summary.json`.']
    for i,item in enumerate(eda['summary']['findings'],1):
        parts.extend([f"## {i}. {item['title']}",item['text'],f"![SIMULASI: {item['title']}](../reports/cp2/figures/{item['figure']})"])
    parts.append('Denominator profil adalah orang; sesi adalah ID-tanggal-sesi; korelasi menggunakan catatan ID-tanggal. '
                 'Korelasi pairwise mengabaikan NA per pasangan; tidak terdefinisi bila varians nol atau data tidak cukup. '
                 'Sampel berulang tidak dianggap observasi independen. Tidak ada inferensi statistik atau training model pada CP2 ini.')
    return '\n\n'.join(parts)+'\n'
