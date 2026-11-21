import {test,expect} from '@playwright/test';

test('injected loader failure clears a previously successful prediction without fallback charts',async({page})=>{
 await page.goto('/#'+encodeURIComponent('Prediksi Tekanan Darah'));
 const submit=page.getByRole('button',{name:'Hitung perkiraan model'});
 await expect(submit).toBeEnabled();
 await submit.click();
 await expect(page.locator('.prediction-charts')).toBeVisible();
 // Deliberate HTTP error injection for the UI; backend rejection is covered separately.
 await page.route(/\/api\/model\/predict\?/,route=>route.fulfill({status:409,json:{detail:'UJI TERKONTROL: artefak model tidak cocok',error_code:'MODEL_INCOMPATIBLE'}}));
 await submit.click();
 await expect(page.getByRole('alert')).toContainText('UJI TERKONTROL');
 await expect(page.locator('.prediction-result')).toHaveCount(0);
 await expect(page.locator('.prediction-charts')).toHaveCount(0);
});
