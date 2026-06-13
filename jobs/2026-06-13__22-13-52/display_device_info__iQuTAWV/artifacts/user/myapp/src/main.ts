import { Device } from '@capacitor/device';

async function displayDeviceInfo() {
  try {
    const info = await Device.getInfo();
    
    const platformEl = document.getElementById('device-platform');
    const osEl = document.getElementById('device-os');
    
    if (platformEl) {
      platformEl.textContent = info.platform;
    }
    if (osEl) {
      osEl.textContent = info.operatingSystem;
    }
  } catch (error) {
    console.error('Error getting device info:', error);
  }
}

// Run on page load
displayDeviceInfo();
