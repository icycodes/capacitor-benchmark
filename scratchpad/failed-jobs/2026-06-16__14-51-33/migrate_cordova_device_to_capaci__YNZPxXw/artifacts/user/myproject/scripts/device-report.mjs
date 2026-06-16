// Node-callable device-info reader using @capacitor/device.
// Provides minimal navigator/window shims so the web implementation can run
// outside a real browser.

// ---- shim navigator/window before importing the plugin ----

const ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

if (typeof globalThis.navigator === 'undefined') {
  globalThis.navigator = {
    userAgent: ua,
    vendor: 'Google Inc.',
    language: 'en-US',
    getBattery: () => Promise.resolve({ level: 1, charging: true }),
  };
}

if (typeof globalThis.window === 'undefined') {
  globalThis.window = globalThis;
}

// ---- import and call the Capacitor Device plugin ----

import { Device } from '@capacitor/device';

const [info, id, battery] = await Promise.all([
  Device.getInfo(),
  Device.getId(),
  Device.getBatteryInfo(),
]);

const result = {
  info: {
    platform: info.platform,
    operatingSystem: info.operatingSystem,
    osVersion: info.osVersion,
    manufacturer: info.manufacturer,
    model: info.model,
    isVirtual: info.isVirtual,
    webViewVersion: info.webViewVersion,
  },
  id: {
    identifier: id.identifier,
  },
  battery: {
    batteryLevel: battery.batteryLevel,
    isCharging: battery.isCharging,
  },
};

process.stdout.write(JSON.stringify(result) + '\n');
