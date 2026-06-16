import { StatusBar, Style } from '@capacitor/status-bar';
import { App } from '@capacitor/app';
import { registerPlugin } from '@capacitor/core';

// ---------------------------------------------------------------------------
// Custom NavBar plugin registration
// The Java counterpart (NavBarPlugin.java) is wired into MainActivity and
// exposes the plugin under the bridge name "NavBar".
// ---------------------------------------------------------------------------
interface NavBarPlugin {
  setColor(options: { color: string }): Promise<void>;
}

const NavBar = registerPlugin<NavBarPlugin>('NavBar');

// ---------------------------------------------------------------------------
// Theme palettes
// ---------------------------------------------------------------------------
const THEMES = {
  dark: {
    style: Style.Dark,           // light (white) status-bar icons on dark bg
    statusBarColor: '#1a1a2e',
    navBarColor: '#1a1a2e',
  },
  light: {
    style: Style.Light,          // dark icons on light bg
    statusBarColor: '#f5f5f5',
    navBarColor: '#f5f5f5',
  },
} as const;

// ---------------------------------------------------------------------------
// applyTheme
// ---------------------------------------------------------------------------

/**
 * Applies a consistent visual theme to both the Android status bar and the
 * navigation bar (system back / home / overview buttons area).
 *
 * Before issuing native commands the function calls App.getInfo() and
 * StatusBar.getInfo() for platform-detection purposes; their results are
 * logged so they can be inspected during development.
 *
 * @param mode - 'dark' for a dark chrome, 'light' for a light chrome.
 */
export async function applyTheme(mode: 'dark' | 'light'): Promise<void> {
  // --- Platform / state detection -----------------------------------------
  const [appInfo, barInfo] = await Promise.all([
    App.getInfo(),
    StatusBar.getInfo(),
  ]);

  console.log('[applyTheme] app info:', appInfo);
  console.log('[applyTheme] current status-bar info:', barInfo);

  // --- Apply theme ---------------------------------------------------------
  const theme = THEMES[mode];

  await StatusBar.setStyle({ style: theme.style });
  await StatusBar.setBackgroundColor({ color: theme.statusBarColor });
  await NavBar.setColor({ color: theme.navBarColor });

  console.log(`[applyTheme] theme "${mode}" applied successfully`);
}
