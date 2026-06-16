// Initial scaffold. The executor must install @capacitor/share v8, render a
// <button id="share-btn"> on the page (here or in index.html), and call
// Share.share({ title: "Demo", text: "Hello from Capacitor", dialogTitle: "Choose" })
// on click.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a Share integration.";
  app.appendChild(note);
}
