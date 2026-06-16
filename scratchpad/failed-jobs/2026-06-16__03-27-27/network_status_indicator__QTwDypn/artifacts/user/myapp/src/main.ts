import { Network } from '@capacitor/network';

const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Network status: ";
  
  const statusSpan = document.createElement("span");
  statusSpan.id = "net-status";
  statusSpan.textContent = "unknown";
  
  note.appendChild(statusSpan);
  app.appendChild(note);

  // Initial network status
  Network.getStatus().then((status) => {
    statusSpan.textContent = status.connected ? "online" : "offline";
  });

  // Listen for network changes
  Network.addListener('networkStatusChange', (status) => {
    statusSpan.textContent = status.connected ? "online" : "offline";
  });
}
