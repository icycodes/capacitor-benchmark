import { CapacitorHttp } from '@capacitor/core';

const fetchBtn = document.getElementById('fetch-btn');
const httpStatus = document.getElementById('http-status');

if (fetchBtn && httpStatus) {
  fetchBtn.addEventListener('click', async () => {
    const url = (window as any).__API_URL__;
    if (!url) {
      console.error('window.__API_URL__ is not defined');
      return;
    }

    try {
      const response = await CapacitorHttp.get({ url });
      httpStatus.textContent = String(response.status);
    } catch (error) {
      console.error('Error fetching with CapacitorHttp:', error);
      httpStatus.textContent = 'Error';
    }
  });
}
