import { CapacitorHttp } from '@capacitor/core';

const app = document.getElementById('app');
if (app) {
  // Clear existing placeholder content
  app.innerHTML = '';

  const btn = document.createElement('button');
  btn.id = 'fetch-btn';
  btn.textContent = 'Fetch Status';
  app.appendChild(btn);

  app.appendChild(document.createTextNode(' '));

  const statusSpan = document.createElement('span');
  statusSpan.id = 'http-status';
  app.appendChild(statusSpan);

  btn.addEventListener('click', async () => {
    const url = (window as any).__API_URL__ as string;
    const response = await CapacitorHttp.get({ url });
    statusSpan.textContent = String(response.status);
  });
}
