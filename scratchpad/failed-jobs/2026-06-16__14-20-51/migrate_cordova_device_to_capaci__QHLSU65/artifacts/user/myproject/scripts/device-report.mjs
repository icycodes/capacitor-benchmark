import { Device } from '@capacitor/device';

if (!globalThis.window) {
  globalThis.window = {};
}
globalThis.window.chrome = {};

Object.defineProperty(globalThis.navigator, 'userAgent', {
  value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
  writable: true,
  configurable: true
});

Object.defineProperty(globalThis.navigator, 'getBattery', {
  value: async () => ({ level: 1.0, charging: true }),
  writable: true,
  configurable: true
});

Object.defineProperty(globalThis.navigator, 'vendor', {
  value: 'Google Inc.',
  writable: true,
  configurable: true
});

async function run() {
  const info = await Device.getInfo();
  const id = await Device.getId();
  const battery = await Device.getBatteryInfo();
  
  const payload = {
    info: {
      platform: info.platform || 'web',
      operatingSystem: info.operatingSystem || 'unknown',
      osVersion: info.osVersion || 'unknown',
      manufacturer: info.manufacturer || 'unknown',
      model: info.model || 'unknown',
      isVirtual: info.isVirtual || false,
      webViewVersion: info.webViewVersion || 'unknown'
    },
    id: {
      identifier: id.identifier || 'unknown'
    },
    battery: {
      batteryLevel: battery.batteryLevel || 1,
      isCharging: battery.isCharging || false
    }
  };
  
  console.log(JSON.stringify(payload));
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
