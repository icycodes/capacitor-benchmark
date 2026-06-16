// Initial scaffold. The executor must populate the page with device info from
// @capacitor/device (Device.getInfo + Device.getLanguageCode).
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a Device plugin integration.";
  app.appendChild(note);
}
