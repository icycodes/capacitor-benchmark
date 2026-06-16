// Shim for Node.js environment to mock browser globals needed by @capacitor/device
const store = {};

globalThis.window = {
  localStorage: {
    getItem: (key) => store[key] || null,
    setItem: (key, val) => { store[key] = val; },
    removeItem: (key) => { delete store[key]; },
    clear: () => { for (const k in store) delete store[k]; }
  },
  chrome: true,
  ApplePaySession: undefined,
  MSStream: undefined
};

if (typeof globalThis.navigator === 'undefined') {
  globalThis.navigator = {};
}

const properties = {
  userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  vendor: "Google Inc.",
  language: "en-US",
  getBattery: async () => ({
    level: 1.0,
    charging: true
  })
};

for (const [key, value] of Object.entries(properties)) {
  Object.defineProperty(globalThis.navigator, key, {
    value: value,
    configurable: true,
    writable: true,
    enumerable: true
  });
}
