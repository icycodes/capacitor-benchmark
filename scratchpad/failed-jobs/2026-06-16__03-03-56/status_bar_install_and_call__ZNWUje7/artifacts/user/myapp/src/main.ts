// Initial scaffold. The executor must install @capacitor/status-bar v8 and
// add calls to StatusBar.setStyle({ style: Style.Dark }) and
// StatusBar.setBackgroundColor({ color: '#222222' }) here (or in another file
// under src/) so that the resulting bundle still contains those calls.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a StatusBar wiring integration.";
  app.appendChild(note);
}
