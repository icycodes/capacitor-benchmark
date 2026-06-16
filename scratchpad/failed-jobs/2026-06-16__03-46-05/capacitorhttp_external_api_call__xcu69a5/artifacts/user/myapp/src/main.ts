// Initial scaffold. The executor must:
//   1. Enable CapacitorHttp in capacitor.config.ts.
//   2. Render a #fetch-btn <button> and a #items <ul> in the page.
//   3. On click, call CapacitorHttp.get({ url: window.__API_URL__ }) and
//      append one <li>{name}</li> per entry of response.data.items.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a CapacitorHttp.get integration.";
  app.appendChild(note);
}
