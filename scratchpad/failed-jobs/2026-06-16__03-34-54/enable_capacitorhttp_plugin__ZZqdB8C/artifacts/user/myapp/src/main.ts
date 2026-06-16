import { CapacitorHttp } from '@capacitor/core';

declare global {
  interface Window {
    __API_URL__: string;
  }
}

const app = document.getElementById('app');
if (app) {
  const btn = document.createElement('button');
  btn.id = 'fetch-btn';
  btn.textContent = 'Fetch';

  const span = document.createElement('span');
  span.id = 'http-status';
  span.textContent = '';

  btn.addEventListener('click', async () => {
    const url = window.__API_URL__;
    const response = await CapacitorHttp.get({ url });
    span.textContent = String(response.status);
  });

  app.appendChild(btn);
  app.appendChild(span);
}