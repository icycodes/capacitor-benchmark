import { Preferences } from "@capacitor/preferences";

const THEME_KEY = "user_theme";
const DARK_CLASS = "dark";

function applyTheme(isDark: boolean): void {
  if (isDark) {
    document.body.classList.add(DARK_CLASS);
  } else {
    document.body.classList.remove(DARK_CLASS);
  }
}

async function loadTheme(): Promise<void> {
  const { value } = await Preferences.get({ key: THEME_KEY });
  const isDark = value === "dark";
  applyTheme(isDark);
}

async function toggleTheme(): Promise<void> {
  const isDark = document.body.classList.contains(DARK_CLASS);
  const newValue = isDark ? "light" : "dark";
  await Preferences.set({ key: THEME_KEY, value: newValue });
  applyTheme(!isDark);
}

function initToggleButton(): void {
  const button = document.getElementById("theme-toggle");
  if (button) {
    button.addEventListener("click", toggleTheme);
  }
}

async function init(): Promise<void> {
  await loadTheme();
  initToggleButton();
}

init();
