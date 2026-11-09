import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const target=process.env.TOBA_API_PROXY_TARGET||'http://localhost:8000';
const proxy={'/api':target,'/health':target};
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy },
  preview: { port:4173, proxy },
});
