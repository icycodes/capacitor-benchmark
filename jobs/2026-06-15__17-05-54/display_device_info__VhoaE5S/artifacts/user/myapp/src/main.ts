import { Device } from '@capacitor/device';

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
