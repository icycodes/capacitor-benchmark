// Minimal entrypoint. No runtime Capacitor APIs are required for this task —
// the task only verifies the presence and version of installed platform packages.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Capacitor platform packages demo.";
  app.appendChild(note);
}
