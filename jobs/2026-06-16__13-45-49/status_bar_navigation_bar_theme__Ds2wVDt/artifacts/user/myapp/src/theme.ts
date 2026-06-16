import { StatusBar, Style } from '@capacitor/status-bar';
import { App } from '@capacitor/app';
import { registerPlugin, Capacitor } from '@capacitor/core';

interface NavBarPlugin {
  setColor(options: { color: string }): Promise<void>;
}

const NavBar = registerPlugin<NavBarPlugin>("NavBar");

export async function applyTheme(mode: 'dark' | 'light'): Promise<void> {
  // Demonstrate platform detection and retrieve info from App and StatusBar
  try {
    const appInfo = await App.getInfo();
    const statusBarInfo = await StatusBar.getInfo();
    console.log(`App info retrieved: ${appInfo.name} (${appInfo.id})`);
    console.log(`Status bar info retrieved: visible=${statusBarInfo.visible}`);
  } catch (error) {
    console.warn('Failed to retrieve app/statusbar info:', error);
  }

  const isAndroid = Capacitor.getPlatform() === 'android';

  if (mode === 'dark') {
    const darkColor = '#121212';
    try {
      await StatusBar.setStyle({ style: Style.Dark });
      await StatusBar.setBackgroundColor({ color: darkColor });
    } catch (error) {
      console.error('Error applying dark theme to status bar:', error);
    }

    if (isAndroid) {
      try {
        await NavBar.setColor({ color: darkColor });
      } catch (error) {
        console.error('Error applying dark theme to navigation bar:', error);
      }
    }
  } else {
    const lightColor = '#FFFFFF';
    try {
      await StatusBar.setStyle({ style: Style.Light });
      await StatusBar.setBackgroundColor({ color: lightColor });
    } catch (error) {
      console.error('Error applying light theme to status bar:', error);
    }

    if (isAndroid) {
      try {
        await NavBar.setColor({ color: lightColor });
      } catch (error) {
        console.error('Error applying light theme to navigation bar:', error);
      }
    }
  }
}
