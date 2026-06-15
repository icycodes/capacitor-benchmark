import { Preferences } from '@capacitor/preferences';

const THEME_KEY = 'user_theme';
type Theme = 'light' | 'dark';

async function getSavedTheme(): Promise<Theme> {
  const { value } = await Preferences.get({ key: THEME_KEY });
  if (value === 'dark') return 'dark';
  return 'light';
}

async function saveTheme(theme: Theme): Promise<void> {
  await Preferences.set({ key: THEME_KEY, value: theme });
}

function applyTheme(theme: Theme): void {
  if (theme === 'dark') {
    document.body.classList.add('dark');
  } else {
    document.body.classList.remove('dark');
  }
}

async function init(): Promise<void> {
  // Load and apply the saved theme before user interacts
  const savedTheme = await getSavedTheme();
  applyTheme(savedTheme);

  const toggleButton = document.getElementById('theme-toggle');
  if (!toggleButton) return;

  toggleButton.addEventListener('click', async () => {
    const isDark = document.body.classList.contains('dark');
    const newTheme: Theme = isDark ? 'light' : 'dark';
    applyTheme(newTheme);
    await saveTheme(newTheme);
  });
}

init();
