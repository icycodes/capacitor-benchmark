import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My Capacitor App',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    hostname: 'myapp.example.com'
  }
};

export default config;
