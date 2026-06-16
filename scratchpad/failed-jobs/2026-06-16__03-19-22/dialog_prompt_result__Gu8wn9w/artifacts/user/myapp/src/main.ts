// Initial scaffold. The executor must install @capacitor/dialog v8 and add a
// <button id="prompt-btn"> plus a <span id="prompt-result"> to the page,
// wire a click handler that calls Dialog.prompt({ title: 'Your name',
// message: 'Enter name' }), and write the resolved value (or the literal
// string "cancelled") into #prompt-result.textContent.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a Dialog.prompt integration.";
  app.appendChild(note);
}
