import { Preferences } from '@capacitor/preferences';

async function initTheme() {
  try {
    const { value } = await Preferences.get({ key: 'user_theme' });
    if (value === 'dark') {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  } catch (error) {
    console.error('Error reading theme from Preferences:', error);
    // Default to light theme on error
    document.body.classList.remove('dark');
  }
}

async function toggleTheme() {
  try {
    const isDark = document.body.classList.toggle('dark');
    await Preferences.set({
      key: 'user_theme',
      value: isDark ? 'dark' : 'light',
    });
  } catch (error) {
    console.error('Error saving theme to Preferences:', error);
  }
}

// Initialize theme
initTheme();

// Wire up toggle button
const button = document.getElementById('theme-toggle');
if (button) {
  button.addEventListener('click', toggleTheme);
}
