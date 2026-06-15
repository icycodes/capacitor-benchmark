import { Device } from '@capacitor/device';

async function init(): Promise<void> {
  const info = await Device.getInfo();

  const platformEl = document.getElementById('device-platform');
  if (platformEl) {
    platformEl.textContent = info.platform;
  }

  const osEl = document.getElementById('device-os');
  if (osEl) {
    osEl.textContent = info.operatingSystem;
  }
}

init();
