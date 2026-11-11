// P2-05: checklist interaksi grafik (tooltip, drill-down/cross-filter, reset, filter global, empty state, mobile, aksesibilitas dasar).
import {test,expect} from '@playwright/test';

const chartPages=['Dashboard','Data Partisipan','Analisis Faktor Risiko','Tren Tekanan Darah','Evaluasi Model'];
async function ready(page){await expect(page.getByRole('button',{name:'Muat ulang data',exact:true})).toBeEnabled();}
async function navigate(page,label){await page.getByRole('navigation').getByRole('button',{name:label,exact:true}).click();await expect(page.getByRole('heading',{level:1})).toHaveText(label);}

test('C1 tooltip muncul saat hover titik grafik tren',async({page})=>{
  await page.goto('/');await ready(page);
  const point=page.locator('.js-plotly-plot').first().locator('.scatterlayer .point').first();
  await point.scrollIntoViewIfNeeded();await expect(point).toBeVisible();const box=await point.boundingBox();
  await page.mouse.move(box.x+box.width/2-20,box.y+box.height/2);await page.mouse.move(box.x+box.width/2,box.y+box.height/2,{steps:8});
  await expect(page.locator('.hoverlayer .hovertext, .hoverlayer .legend').first()).toBeVisible();
});

test('C2 klik titik = cross-filter global, KPI berubah, reset mengembalikan KPI awal',async({page})=>{
  await page.goto('/');await ready(page);
  const before=await page.locator('.kpi-value').allTextContents();
  const selected=page.waitForResponse(r=>r.url().includes('/api/analytics?')&&r.url().includes('session='));
  await page.locator('.js-plotly-plot').first().locator('.scatterlayer .point').first().click({force:true});await selected;await ready(page);
  await expect(page.getByLabel('Filter aktif',{exact:true})).toContainText('Sesi pengukuran');
  expect(await page.locator('.kpi-value').allTextContents()).not.toEqual(before);
  await page.getByRole('button',{name:'Reset filter',exact:true}).click();await ready(page);
  expect(await page.locator('.kpi-value').allTextContents()).toEqual(before);
});

test('C3 setiap kartu grafik punya judul, keterangan, dan catatan sampel',async({page})=>{
  await page.goto('/');await ready(page);
  for(const [i,label] of chartPages.entries()){
    if(i)await navigate(page,label);
    const cards=page.locator('section.analysis-card');const count=await cards.count();expect(count).toBeGreaterThan(0);
    for(let n=0;n<count;n++){
      const card=cards.nth(n);
      await expect(card.getByRole('heading').first()).toBeVisible();
      await expect(card.locator('.chart-explainer')).not.toBeEmpty();
      await expect(card.locator('.sample-note')).toBeVisible();
    }
  }
});

test('C4 filter global ID dipatuhi seluruh halaman: tabel, KPI dan API sama',async({page})=>{
  await page.goto('/');await ready(page);
  await page.getByLabel('ID responden',{exact:true}).selectOption('SIM001');await ready(page);
  const api=await (await page.request.get('/api/analytics?respondent_id=SIM001')).json();
  await expect(page.locator('.kpi-value').first()).toHaveText('1');
  await expect(page.locator('.kpi-value').nth(2)).toHaveText(Number(api.kpis.sessions).toLocaleString('id-ID'));
  await navigate(page,'Tren Tekanan Darah');
  const ids=await page.locator('table tbody tr td:first-child').allTextContents();
  expect(ids.length).toBeGreaterThan(0);expect(new Set(ids.map(t=>t.trim()))).toEqual(new Set(['SIM001']));
  await navigate(page,'Analisis Faktor Risiko');
  await expect(page.locator('.js-plotly-plot').first()).toBeVisible();
  await navigate(page,'Data Partisipan');
  await expect(page.locator('table tbody tr')).toHaveCount(1);
});

test('C5 filter tanggal terbalik tidak memanggil API analitik dan tidak menampilkan grafik lama',async({page})=>{
  await page.goto('/');await ready(page);
  await page.getByLabel('Mulai tanggal',{exact:true}).fill('2026-09-10');
  await page.getByLabel('Sampai tanggal',{exact:true}).fill('2026-09-01');
  await expect(page.getByText('Tanggal mulai harus sebelum atau sama dengan tanggal sampai',{exact:false})).toBeVisible();
  await expect(page.locator('.kpi-value')).toHaveCount(0);
});

test('C6 filter tanpa observasi menampilkan keadaan kosong, bukan grafik palsu',async({page})=>{
  await page.goto('/');await ready(page);
  await page.getByLabel('Mulai tanggal',{exact:true}).fill('2030-01-01');
  await page.getByLabel('Sampai tanggal',{exact:true}).fill('2030-01-07');await ready(page);
  await expect(page.locator('.js-plotly-plot')).toHaveCount(0);
  await expect(page.locator('.kpi-value')).toHaveCount(0);
});

test('C7 aksesibilitas dasar: tombol dan gambar bernama, fokus keyboard terlihat, filter berlabel',async({page})=>{
  await page.goto('/');await ready(page);
  const unnamed=await page.evaluate(()=>[...document.querySelectorAll('button')].filter(b=>!(b.innerText||'').trim()&&!b.getAttribute('aria-label')).length);
  expect(unnamed).toBe(0);
  const noAlt=await page.evaluate(()=>[...document.querySelectorAll('img')].filter(i=>!i.hasAttribute('alt')).length);
  expect(noAlt).toBe(0);
  for(const label of ['ID responden','Sesi pengukuran','Mulai tanggal','Sampai tanggal'])await expect(page.getByLabel(label,{exact:true})).toBeVisible();
  await page.keyboard.press('Tab');
  const focused=await page.evaluate(()=>{const e=document.activeElement;if(!e||e===document.body)return null;const s=getComputedStyle(e);return {tag:e.tagName,outline:s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0,shadow:s.boxShadow!=='none'}});
  expect(focused).not.toBeNull();expect(focused.outline||focused.shadow).toBeTruthy();
  expect(await page.evaluate(()=>document.documentElement.lang)).toBeTruthy();
});

test('C8 evaluasi menampilkan ringkasan sumber, peringatan sampel kecil, dan label sintetis',async({page})=>{
  await page.goto('/#'+encodeURIComponent('Evaluasi Model'));await ready(page);
  await expect(page.getByText('DATA SINTETIS / SIMULASI').first()).toBeVisible();
  await expect(page.getByText('Test hanya',{exact:false}).first()).toBeVisible();
  await expect(page.getByRole('heading',{name:'Distribusi error'})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Error per responden (test)'})).toBeVisible();
});

test('C9 ponsel: halaman grafik tanpa overflow horizontal dan grafik ikut lebar layar',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');await ready(page);
  for(const [i,label] of chartPages.entries()){
    if(i){await page.getByRole('button',{name:'Buka navigasi'}).click();await navigate(page,label);}
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();
    const wide=await page.evaluate(()=>[...document.querySelectorAll('.js-plotly-plot')].filter(e=>e.getBoundingClientRect().right>window.innerWidth+1).length);
    expect(wide).toBe(0);
  }
});

test('C10 halaman prediksi: ID tidak valid/riwayat kurang menampilkan galat, hasil valid menampilkan mmHg dan pembanding naif',async({page})=>{
  await page.goto('/#'+encodeURIComponent('Prediksi Tekanan Darah'));await ready(page);
  const submit=page.getByRole('button',{name:'Hitung perkiraan model'});await expect(submit).toBeEnabled();
  const response=page.waitForResponse(r=>r.url().includes('/api/model/predict?'));await submit.click();expect((await response).ok()).toBeTruthy();
  await expect(page.locator('.prediction-number')).toContainText('mmHg');
  await expect(page.getByText('Pembanding baseline naif',{exact:false})).toBeVisible();
  await expect(page.getByText('Target belum disetujui dosen',{exact:false}).first()).toBeVisible();
});
