import { Preferences } from "@capacitor/preferences";

async function saveTheme(theme: "dark" | "light"): Promise<void> {
  await Preferences.set({ key: "user_theme", value: theme });
}

async function loadTheme(): Promise<string | null> {
  const { value } = await Preferences.get({ key: "user_theme" });
  return value;
}

const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Capacitor v7 -> v8 upgrade demo.";
  app.appendChild(note);
}

// Expose helpers on window for ad-hoc inspection.
(window as unknown as Record<string, unknown>).saveTheme = saveTheme;
(window as unknown as Record<string, unknown>).loadTheme = loadTheme;
