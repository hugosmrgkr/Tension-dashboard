const PREFIX = '/api';

export async function api(path, options = {}) {
  const response = await fetch(PREFIX + path, options);
  if (!response.ok) {
    let msg = `HTTP ${response.status}`;
    try {
      const error = await response.json();
      msg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail ?? error);
    } catch (_) { /* no JSON error */ }
    throw new Error(msg);
  }
  return response.json();
}

export function queryString(filters = {}, extra = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...filters, ...extra })) {
    if (value !== undefined && value !== null && value !== '' && value !== 'Semua' && value !== 'Semua Kecamatan') {
      params.set(key, String(value));
    }
  }
  return params.toString() ? `?${params}` : '';
}

export const fmt = (value, digits = 1) => value == null ? '–' : Number(value).toLocaleString('id-ID', { minimumFractionDigits: digits, maximumFractionDigits: digits });
export const whole = (value) => value == null ? '–' : Number(value).toLocaleString('id-ID', { maximumFractionDigits: 0 });
export const dateID = (date) => date ? new Date(date + 'T00:00:00').toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '–';
export const LABELS = ['Normal', 'Pra-hipertensi', 'Hipertensi Tahap 1', 'Hipertensi Tahap 2'];
export const COLORS = ['#22b36b', '#fbbf3a', '#ef5b5b', '#d6232f'];
export const colorFor = status => COLORS[Math.max(0, LABELS.indexOf(status))];

export async function download(url, name) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Gagal mengunduh (${response.status})`);
  const blob = await response.blob();
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href; link.download = name;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(href), 2000);
}
