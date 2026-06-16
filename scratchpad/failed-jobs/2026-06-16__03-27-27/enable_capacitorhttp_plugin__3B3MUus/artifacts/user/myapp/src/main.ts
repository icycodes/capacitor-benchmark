import { CapacitorHttp } from '@capacitor/core';

declare global {
  interface Window {
    __API_URL__: string;
  }
}

const fetchBtn = document.getElementById('fetch-btn');
const httpStatus = document.getElementById('http-status');

if (fetchBtn && httpStatus) {
  fetchBtn.addEventListener('click', async () => {
    try {
      const url = window.__API_URL__;
      if (url) {
        const response = await CapacitorHttp.get({ url });
        httpStatus.textContent = String(response.status);
      }
    } catch (e) {
      console.error(e);
      httpStatus.textContent = 'Error';
    }
  });
}
