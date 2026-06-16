// Initial scaffold. The executor must extend this entry script so that it
// installs the background-aware geolocation tracker and exposes it as
// `window.tracker` (with async `start`, `stop`, and `getLatest` methods).
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Implement the background-aware geolocation tracker.";
  app.appendChild(note);
}
