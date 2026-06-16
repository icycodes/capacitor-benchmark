import { registerPlugin } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { App } from '@capacitor/app';

export interface NavBarPlugin {
  setColor(options: { color: string }): Promise<void>;
}

const NavBar = registerPlugin<NavBarPlugin>("NavBar");

export async function applyTheme(mode: 'dark' | 'light') {
  await App.getInfo();
  await StatusBar.getInfo();

  if (mode === 'dark') {
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#000000' });
    await NavBar.setColor({ color: '#000000' });
  } else {
    await StatusBar.setStyle({ style: Style.Light });
    await StatusBar.setBackgroundColor({ color: '#ffffff' });
    await NavBar.setColor({ color: '#ffffff' });
  }
}
