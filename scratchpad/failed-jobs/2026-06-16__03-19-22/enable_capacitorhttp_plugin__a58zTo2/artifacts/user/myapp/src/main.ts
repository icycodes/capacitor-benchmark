import { CapacitorHttp } from '@capacitor/core';

declare global {
  interface Window {
    __API_URL__: string;
  }
}

const btn = document.getElementById('fetch-btn') as HTMLButtonElement;
const statusSpan = document.getElementById('http-status') as HTMLSpanElement;

btn.addEventListener('click', async () => {
  const url = window.__API_URL__;
  const response = await CapacitorHttp.get({ url });
  statusSpan.textContent = String(response.status);
});
