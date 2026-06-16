// Initial scaffold. The executor must install @capacitor/app v8, add a
// `<span id="app-state">` element to the page, and subscribe to
// App.addListener('appStateChange', ({ isActive }) => ...) so that the span's
// textContent reads "active" or "inactive" depending on isActive.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with the App state visibility integration.";
  app.appendChild(note);
}
