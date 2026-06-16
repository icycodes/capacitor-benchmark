import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.cookiesession',
  appName: 'CookieSession',
  webDir: 'dist',
  plugins: {
    CapacitorCookies: {
      enabled: true,
    },
  },
};

export default config;
