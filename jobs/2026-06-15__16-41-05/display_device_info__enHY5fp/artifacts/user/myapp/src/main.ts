import { Device } from '@capacitor/device';

async function init() {
  const info = await Device.getInfo();

  const app = document.getElementById("app");
  if (app) {
    app.innerHTML = `
      <h1>Device Demo</h1>
      <p>Platform: <span id="device-platform">${info.platform}</span></p>
      <p>OS: <span id="device-os">${info.operatingSystem}</span></p>
    `;
  }
}

init();
