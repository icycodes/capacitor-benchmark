import { registerPlugin } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { App } from '@capacitor/app';

// ---------------------------------------------------------------------------
// Custom NavBar plugin – drives the Android navigation bar colour via the
// native NavBarPlugin (Java) registered in MainActivity.
// ---------------------------------------------------------------------------
export interface NavBarPlugin {
  setColor(options: { color: string }): Promise<void>;
}

const NavBar = registerPlugin<NavBarPlugin>('NavBar');

// ---------------------------------------------------------------------------
// applyTheme – single entry point for syncing web theme with native chrome
// ---------------------------------------------------------------------------
export async function applyTheme(mode: 'dark' | 'light'): Promise<void> {
  // Demonstrate platform detection by fetching platform info (logged or used
  // internally before issuing theme commands).
  const [appInfo, statusBarInfo] = await Promise.all([
    App.getInfo(),
    StatusBar.getInfo(),
  ]);
  console.log('[theme] Platform info:', { appInfo, statusBarInfo });

  const isDark = mode === 'dark';

  // Pair each mode with a sensible hex background colour.
  const bgColor = isDark ? '#1a1a2e' : '#f0f0f5';
  const style = isDark ? Style.Dark : Style.Light;

  // Update status bar
  await StatusBar.setStyle({ style });
  await StatusBar.setBackgroundColor({ color: bgColor });

  // Update Android navigation bar (no-op on other platforms)
  await NavBar.setColor({ color: bgColor });
}
