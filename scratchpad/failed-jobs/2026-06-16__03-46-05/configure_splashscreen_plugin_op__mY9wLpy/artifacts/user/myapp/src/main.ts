// Initial scaffold. The executor must install @capacitor/splash-screen@^8,
// configure plugins.SplashScreen in capacitor.config.ts, and call
// SplashScreen.hide() from a TS module after the DOM is ready.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a SplashScreen.hide() call.";
  app.appendChild(note);
}
