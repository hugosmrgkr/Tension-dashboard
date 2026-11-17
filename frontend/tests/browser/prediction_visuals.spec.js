import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';

const screenshotDir=(process.env.CP3_REPORT_DIR||'../reports/hugo_stage3')+'/screenshots';
async function openPrediction(page){
 await page.goto('/#'+encodeURIComponent('Prediksi Tekanan Darah'));
 await expect(page.getByRole('button',{name:'Hitung perkiraan model'})).toBeEnabled();
}
async function predict(page){
 const response=page.waitForResponse(r=>r.url().includes('/api/model/predict?'));
 await page.getByRole('button',{name:'Hitung perkiraan model'}).click();
 const result=await response;
 expect(result.ok()).toBeTruthy();
 await expect(page.locator('.prediction-history .js-plotly-plot')).toBeVisible();
 return result.json();
}

test('prediction desktop charts match API history and one aggregate forecast',async({page})=>{
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await openPrediction(page);
 const data=await predict(page);
 expect(data.history_daily).toHaveLength(7);
 const history=await page.locator('.prediction-history .js-plotly-plot').evaluate(el=>el.data.map(trace=>({name:trace.name,x:trace.x,y:trace.y})));
 expect(history.map(trace=>trace.name)).toEqual(['SBP','DBP']);
 expect(history[0].x).toEqual(data.history_daily.map(row=>row.date));
 expect(history[0].y).toEqual(data.history_daily.map(row=>row.sbp));
 expect(history[1].y).toEqual(data.history_daily.map(row=>row.dbp));
 expect(history[0].x.every(date=>date<=data.last_date)).toBeTruthy();
 const summary=await page.locator('.prediction-comparison .js-plotly-plot').evaluate(el=>({x:el.data[0].x,y:el.data[0].y}));
 expect(summary.x).toEqual(['Model','Baseline naif']);
 expect(summary.y).toEqual([data.prediction_mmHg,data.reference_naive_mmHg]);
 await expect(page.getByText('bukan tujuh prediksi harian',{exact:false})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
 await mkdir(screenshotDir,{recursive:true});
 await page.screenshot({path:screenshotDir+'/prediction-desktop.png',fullPage:true});
 expect(errors).toEqual([]);
});

test('prediction origin limits history; insufficient history never displays stale charts',async({page})=>{
 await openPrediction(page);await predict(page);
 const meta=await (await page.request.get('/api/meta')).json();
 await page.getByLabel('Tanggal origin prediksi').fill(meta.min_date);
 await expect(page.locator('.prediction-charts')).toHaveCount(0);
 const invalid=page.waitForResponse(r=>r.url().includes('/api/model/predict?'));
 await page.getByRole('button',{name:'Hitung perkiraan model'}).click();
 expect((await invalid).status()).toBe(422);
 await expect(page.getByRole('alert')).toContainText('berturut');
 await expect(page.locator('.prediction-charts')).toHaveCount(0);
 const origin=new Date(meta.min_date+'T00:00:00Z');origin.setUTCDate(origin.getUTCDate()+6);
 const date=origin.toISOString().slice(0,10);
 await page.getByLabel('Tanggal origin prediksi').fill(date);
 const data=await predict(page);
 expect(data.last_date).toBe(date);
 expect(data.history_daily.every(row=>row.date<=date)).toBeTruthy();
});

test('prediction mobile charts fit screen and ID change clears old results',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await openPrediction(page);await predict(page);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
 const wide=await page.locator('.prediction-charts .js-plotly-plot').evaluateAll(elements=>elements.some(el=>el.getBoundingClientRect().right>innerWidth+1));
 expect(wide).toBeFalsy();
 await mkdir(screenshotDir,{recursive:true});
 await page.screenshot({path:screenshotDir+'/prediction-mobile.png',fullPage:true});
 await page.locator('.prediction-history').scrollIntoViewIfNeeded();
 await page.screenshot({path:screenshotDir+'/prediction-mobile-history.png'});
 const options=await page.getByLabel('ID prediksi model').locator('option').evaluateAll(elements=>elements.map(el=>el.value));
 expect(options.length).toBeGreaterThan(1);
 await page.getByLabel('ID prediksi model').selectOption(options[1]);
 await expect(page.locator('.prediction-charts')).toHaveCount(0);
 await expect(page.locator('.prediction-result')).toHaveCount(0);
});
