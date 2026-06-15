import { Preferences } from '@capacitor/preferences';

async function initTheme() {
  const { value } = await Preferences.get({ key: 'user_theme' });
  const theme = value === 'dark' ? 'dark' : 'light';
  
  if (theme === 'dark') {
    document.body.classList.add('dark');
  } else {
    document.body.classList.remove('dark');
  }

  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', async () => {
      const isDark = document.body.classList.contains('dark');
      const newTheme = isDark ? 'light' : 'dark';
      
      if (newTheme === 'dark') {
        document.body.classList.add('dark');
      } else {
        document.body.classList.remove('dark');
      }
      
      await Preferences.set({ key: 'user_theme', value: newTheme });
    });
  }
}

initTheme();
