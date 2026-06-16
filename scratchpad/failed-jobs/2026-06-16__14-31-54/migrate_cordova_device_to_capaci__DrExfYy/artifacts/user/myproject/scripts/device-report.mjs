// Node-commandable script that reads device info via @capacitor/device.
// Sets up minimal browser shims so the web implementation can execute outside a real browser.

// -- Navigator / window shims required by @capacitor/device web implementation --
// Node.js 22+ ships a built-in navigator; we must override its properties rather
// than check for existence.

const mockUserAgent =
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

if (typeof globalThis.navigator === 'undefined') {
  globalThis.navigator = {};
}

// Override userAgent so the Capacitor web plugin can parse it.
Object.defineProperty(globalThis.navigator, 'userAgent', {
  value: mockUserAgent,
  writable: true,
  configurable: true,
});

if (!globalThis.navigator.vendor) {
  globalThis.navigator.vendor = 'Google Inc.';
}

if (!globalThis.navigator.language) {
  globalThis.navigator.language = 'en-US';
}

if (!globalThis.navigator.getBattery) {
  globalThis.navigator.getBattery = async () => ({ level: 1, charging: true });
}

if (typeof globalThis.window === 'undefined') {
  globalThis.window = globalThis;
}

if (!globalThis.window.localStorage) {
  const store = {};
  globalThis.window.localStorage = {
    getItem: (key) => store[key] ?? null,
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { for (const k in store) delete store[k]; },
  };
}

if (!globalThis.window.chrome) {
  globalThis.window.chrome = true;
}

import { Device } from '@capacitor/device';

const [info, id, battery] = await Promise.all([
  Device.getInfo(),
  Device.getId(),
  Device.getBatteryInfo(),
]);

const report = {
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

console.log(JSON.stringify(report));