import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My Native App',
  webDir: 'dist',
  ios: {
    contentInset: 'always',
  },
};

export default config;
