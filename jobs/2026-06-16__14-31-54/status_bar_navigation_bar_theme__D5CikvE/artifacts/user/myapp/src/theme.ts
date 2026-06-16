import { StatusBar, Style } from '@capacitor/status-bar';
import { App } from '@capacitor/app';
import { registerPlugin } from '@capacitor/core';

interface NavBarPlugin {
  setColor(options: { color: string }): Promise<void>;
}

const NavBar = registerPlugin<NavBarPlugin>('NavBar');

// Demonstrate platform detection before issuing theme commands
App.getInfo().then(info => {
  console.log('App info:', info);
});

StatusBar.getInfo().then(info => {
  console.log('StatusBar info:', info);
});

export async function applyTheme(mode: 'dark' | 'light'): Promise<void> {
  if (mode === 'dark') {
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#1A1A2E' });
    await NavBar.setColor({ color: '#1A1A2E' });
  } else {
    await StatusBar.setStyle({ style: Style.Light });
    await StatusBar.setBackgroundColor({ color: '#FFFFFF' });
    await NavBar.setColor({ color: '#FFFFFF' });
  }
}