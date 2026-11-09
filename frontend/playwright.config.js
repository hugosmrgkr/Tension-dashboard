import {defineConfig} from '@playwright/test';
const report=process.env.CP3_REPORT_DIR||'../reports/cp3_stage2';
const external=process.env.CP3_BROWSER_BASE_URL;

export default defineConfig({
  testDir:'./tests/browser',workers:1,timeout:90000,
  outputDir:report+'/browser-artifacts',
  reporter:[['list'],['json',{outputFile:report+'/browser-results.json'}]],
  use:{baseURL:external||'http://127.0.0.1:4173',channel:process.env.PLAYWRIGHT_CHANNEL||(process.platform==='win32'?'msedge':undefined),
    viewport:{width:1440,height:1000},screenshot:'only-on-failure',trace:'retain-on-failure'},
  webServer:external?undefined:{command:'npm run preview -- --host 127.0.0.1 --port 4173 --strictPort',url:'http://127.0.0.1:4173',reuseExistingServer:false,timeout:30000},
});
