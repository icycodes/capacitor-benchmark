/**
 * device-report.mjs
 *
 * Node-callable script that uses @capacitor/device to print a single JSON
 * object on stdout with device info, device id, and battery info.
 *
 * Because @capacitor/device's web implementation reads from browser globals
 * (navigator, window, localStorage) we install minimal shims before
 * importing the plugin so it can execute outside a real browser.
 */

// ── Minimal browser-global shims ─────────────────────────────────────────────
// Must be done before importing @capacitor/device (top-level await happens at
// module evaluation time, so top-of-file assignment is enough).

// 1. window alias
if (typeof globalThis.window === 'undefined') {
  Object.defineProperty(globalThis, 'window', {
    value: globalThis,
    writable: true,
    configurable: true,
  });
}

// 2. Patch navigator properties that DeviceWeb.getInfo() / getBatteryInfo()
//    require. Node.js 22+ ships a read-only `navigator` object, so we can't
//    reassign it; instead we define (or redefine) individual properties.
const _navProps = {
  // A realistic Chrome-on-Linux UA so the UA parser returns sensible values
  userAgent: {
    value:
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' +
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    writable: true,
    configurable: true,
  },
  vendor: { value: 'Google Inc.', writable: true, configurable: true },
  getBattery: {
    value: () => Promise.resolve({ level: 1, charging: true }),
    writable: true,
    configurable: true,
  },
};

for (const [prop, descriptor] of Object.entries(_navProps)) {
  if (
    !Object.prototype.hasOwnProperty.call(navigator, prop) ||
    !navigator[prop]
  ) {
    try {
      Object.defineProperty(globalThis.navigator, prop, descriptor);
    } catch (_) {
      // Fallback: direct assignment (may silently fail on non-writable props)
      try { globalThis.navigator[prop] = descriptor.value; } catch (_2) {}
    }
  }
}

// 3. localStorage shim (DeviceWeb.getUid uses it)
if (!globalThis.window.localStorage) {
  const _store = {};
  Object.defineProperty(globalThis.window, 'localStorage', {
    value: {
      getItem: (k) => (Object.prototype.hasOwnProperty.call(_store, k) ? _store[k] : null),
      setItem: (k, v) => { _store[k] = String(v); },
    },
    writable: true,
    configurable: true,
  });
}

// 4. window.chrome shim so the Chrome branch of the UA parser is used and
//    webViewVersion is populated (Chrome UA contains "Chrome/MAJOR.MINOR").
if (!globalThis.window.chrome) {
  Object.defineProperty(globalThis.window, 'chrome', {
    value: {},
    writable: true,
    configurable: true,
  });
}

// ── Import plugin (after shims are in place) ─────────────────────────────────

import { Device } from '@capacitor/device';

// ── Gather information ────────────────────────────────────────────────────────

const [info, id, battery] = await Promise.all([
  Device.getInfo(),
  Device.getId(),
  Device.getBatteryInfo(),
]);

// ── Emit result ───────────────────────────────────────────────────────────────

const result = {
  info: {
    platform: info.platform,
    operatingSystem: info.operatingSystem,
    osVersion: info.osVersion ?? '',
    manufacturer: info.manufacturer ?? '',
    model: info.model ?? '',
    isVirtual: typeof info.isVirtual === 'boolean' ? info.isVirtual : false,
    webViewVersion: info.webViewVersion ?? '',
  },
  id: {
    identifier: id.identifier,
  },
  battery: {
    batteryLevel: typeof battery.batteryLevel === 'number' ? battery.batteryLevel : 1,
    isCharging: typeof battery.isCharging === 'boolean' ? battery.isCharging : false,
  },
};

process.stdout.write(JSON.stringify(result) + '\n');
