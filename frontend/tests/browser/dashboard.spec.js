import {test,expect} from '@playwright/test';
import {mkdir,readFile} from 'node:fs/promises';

const pages=['Dashboard','Data Partisipan','Analisis Faktor Risiko','Tren Tekanan Darah','Prediksi Tekanan Darah','Evaluasi Model','Laporan & Ringkasan','Kelola Data'];
const screenshotDir=(process.env.CP3_REPORT_DIR||'../reports/cp3_stage2')+'/screenshots';
async function ready(page){await expect(page.getByRole('button',{name:'Muat ulang data',exact:true})).toBeEnabled();}
async function navigate(page,label){await page.getByRole('navigation').getByRole('button',{name:label,exact:true}).click();await expect(page.getByRole('heading',{level:1})).toHaveText(label);}
async function noOverflow(page){expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();}

test('verified comparison scores match raw predictions and evaluation UI (P2-03)',async({page})=>{
  await page.goto('/#'+encodeURIComponent('Evaluasi Model'));await ready(page);
  const model=await (await page.request.get('/api/model/comparison')).json();
  expect(model.available).toBe(true);expect(model.artifact_integrity_verified).toBe(true);
  expect(model.target_approved).toBe(false);expect(model.leakage_audit.test_overlapping_target_id_days).toBe(0);
  await expect(page.getByText(model.run_id,{exact:false}).first()).toBeVisible();
  const key=name=>name.toLowerCase().replace(/[ -]/g,'_');
  for(const row of model.comparison){
    const mean=model.actual_vs_predicted.reduce((sum,r)=>sum+Math.abs(r.actual-r[key(row.model)]),0)/model.actual_vs_predicted.length;
    expect(mean).toBeCloseTo(row.test.mae,10);
    const formatted=Number(row.test.mae).toLocaleString('id-ID',{minimumFractionDigits:3,maximumFractionDigits:3});
    await expect(page.getByRole('cell',{name:formatted,exact:true}).first()).toBeVisible();
  }
});

test('8 desktop pages render real read-only PostgreSQL data and the baseline API',async({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await mkdir(screenshotDir,{recursive:true});
  await page.goto('/');await ready(page);
  await expect(page.locator('.brand-logo')).toBeVisible();
  expect(await page.locator('.brand-logo').evaluate(image=>image.complete&&image.naturalWidth>0)).toBeTruthy();
  const response=await page.request.get('/api/analytics');expect(response.ok()).toBeTruthy();const data=await response.json();
  expect(data.empty).toBe(false);
  await expect(page.locator('.kpi-value').first()).toHaveText(Number(data.kpis.respondents).toLocaleString('id-ID'));
  for(const [i,label] of pages.entries()){
    if(i)await navigate(page,label);
    if(label==='Prediksi Tekanan Darah'){
      const submit=page.getByRole('button',{name:'Hitung perkiraan model'});await expect(submit).toBeEnabled();
      const result=page.waitForResponse(r=>r.url().includes('/api/model/predict'));
      await submit.click();expect((await result).ok()).toBeTruthy();await expect(page.locator('.prediction-number')).toContainText('mmHg');
    }
    if(label==='Evaluasi Model')await expect(page.getByRole('heading',{name:'Tabel metrik perbandingan'})).toBeVisible();
    await expect(page.locator('.source-banner')).toContainText('DATA SINTETIS / SIMULASI');
    await noOverflow(page);
    await page.screenshot({path:`${screenshotDir}/desktop-${i+1}.png`,fullPage:true});
  }
  expect(errors).toEqual([]);
});

test('chart cross-filter, date/ID/session filters and CSV download share the same scope',async({page})=>{
  await page.goto('/');await ready(page);
  const first=page.locator('.js-plotly-plot').first();await expect(first.locator('.scatterlayer .point').first()).toBeVisible();
  const selected=page.waitForResponse(r=>r.url().includes('/api/analytics?')&&r.url().includes('session='));
  await first.locator('.scatterlayer .point').first().click({force:true});await selected;await ready(page);
  await expect(page.getByLabel('Filter aktif',{exact:true})).toContainText('Sesi pengukuran');
  await page.getByRole('button',{name:'Reset filter',exact:true}).click();await ready(page);
  await page.getByLabel('ID responden',{exact:true}).selectOption('SIM001');await ready(page);
  await page.getByLabel('Sesi pengukuran',{exact:true}).selectOption('Malam');await ready(page);
  await page.getByLabel('Mulai tanggal',{exact:true}).fill('2026-09-01');await ready(page);
  await page.getByLabel('Sampai tanggal',{exact:true}).fill('2026-09-03');await ready(page);
  await expect(page.locator('.kpi-value').nth(1)).toHaveText('3');await expect(page.locator('.kpi-value').nth(2)).toHaveText('3');
  await navigate(page,'Kelola Data');
  const exported=page.waitForResponse(r=>r.url().includes('/api/data/export/sessions?'));
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Sesi tensi',exact:true}).click();const downloaded=await download;
  const response=await exported;expect(response.url()).toContain('respondent_id=SIM001');expect(response.url()).toContain('session=Malam');
  expect(await downloaded.failure()).toBeNull();
  const csv=await readFile(await downloaded.path(),'utf-8');expect(csv.trim().split(/\r?\n/)).toHaveLength(4);expect(csv).not.toContain(',Pagi,');
});

test('province chart drills into a city and demographic filters remain global',async({page})=>{
  await page.goto('/');await ready(page);await navigate(page,'Data Partisipan');
  const chart=page.locator('section.card').filter({has:page.getByRole('heading',{name:'Sebaran responden menurut provinsi',exact:true})});
  const selected=page.waitForResponse(r=>r.url().includes('/api/analytics?')&&r.url().includes('province='));
  await chart.locator('.barlayer .point path').first().click({force:true});await selected;await ready(page);
  const province=await page.getByLabel('Provinsi',{exact:true}).inputValue();expect(province).not.toBe('');
  const meta=await (await page.request.get('/api/meta')).json();
  const city=meta.cities_by_province[province][0];await page.getByLabel('Kabupaten/Kota',{exact:true}).selectOption(city);await ready(page);
  const scoped=await (await page.request.get('/api/analytics?'+new URLSearchParams({province,city}))).json();
  expect(scoped.participants.every(row=>row.province===province&&row.city===city)).toBeTruthy();
  await navigate(page,'Dashboard');await expect(page.getByLabel('Filter aktif',{exact:true})).toContainText(city);
  await expect(page.locator('.kpi-value').first()).toHaveText(Number(scoped.kpis.respondents).toLocaleString('id-ID'));
});

test('mobile layout and navigation work on all 8 pages without horizontal overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');await ready(page);
  await expect(page.getByRole('button',{name:'Tampilkan filter',exact:true})).toHaveAttribute('aria-expanded','false');
  await page.getByRole('button',{name:'Tampilkan filter',exact:true}).click();await expect(page.getByLabel('ID responden',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Sembunyikan filter',exact:true}).click();
  await page.screenshot({path:`${screenshotDir}/mobile-viewport.png`,fullPage:false});
  for(const [i,label] of pages.entries()){
    if(i){await page.getByRole('button',{name:'Buka navigasi'}).click();await navigate(page,label);await expect(page.locator('.sidebar')).not.toHaveClass(/open/);}
    await noOverflow(page);await page.screenshot({path:`${screenshotDir}/mobile-${i+1}.png`,fullPage:true});
  }
  await page.getByRole('button',{name:'Buka navigasi'}).click();await page.keyboard.press('Escape');await expect(page.locator('.sidebar')).not.toHaveClass(/open/);
});

test('all 8 pages show an informative empty state without KPI or charts',async({page})=>{
  await page.route('**/api/meta',route=>route.fulfill({json:{warehouse_empty:true,source_kind:'empty',access_restricted:false,message:'Warehouse belum berisi data. Jalankan ETL manual setelah validasi.',respondent_ids:[],participants:0,daily_records:0,session_records:0}}));
  await page.route('**/api/analytics*',route=>route.fulfill({json:{empty:true,empty_reason:'warehouse_empty',trend:[],kpis:{mean_sbp:null}}}));
  await page.goto('/');await ready(page);
  for(const [i,label] of pages.entries()){
    if(i)await navigate(page,label);
    await expect(page.getByText('Warehouse belum berisi data. Jalankan ETL manual setelah validasi.',{exact:true})).toHaveCount(2);
    await expect(page.locator('.kpi-value')).toHaveCount(0);await expect(page.locator('.js-plotly-plot')).toHaveCount(0);
  }
  await page.screenshot({path:`${screenshotDir}/empty.png`,fullPage:true});
});

test('API errors and filters with no observations never fabricate charts',async({page})=>{
  await page.route('**/api/analytics*',route=>route.fulfill({status:503,json:{detail:'Warehouse tidak dapat dibaca'}}));
  await page.goto('/');await ready(page);await expect(page.getByRole('alert')).toContainText('Warehouse tidak dapat dibaca');await expect(page.locator('.js-plotly-plot')).toHaveCount(0);
  await page.unroute('**/api/analytics*');
  await page.route('**/api/analytics*',route=>route.fulfill({json:{empty:true,empty_reason:'filters_empty',message:'Tidak ada catatan pada filter aktif.',session_rows:[],participants:[],kpis:{mean_sbp:null}}}));
  await page.getByRole('button',{name:'Coba baca ulang'}).click();await ready(page);
  await expect(page.getByText('Tidak ada catatan pada filter aktif.',{exact:true})).toBeVisible();await expect(page.locator('.kpi-value')).toHaveCount(0);
});
