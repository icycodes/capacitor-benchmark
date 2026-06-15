import { Device } from '@capacitor/device';

const app = document.getElementById('app');

async function init() {
  const info = await Device.getInfo();
  const platformEl = document.getElementById('device-platform');
  const osEl = document.getElementById('device-os');
  if (platformEl) {
    platformEl.textContent = info.platform;
  }
  if (osEl) {
    osEl.textContent = info.operatingSystem;
  }
}

init();