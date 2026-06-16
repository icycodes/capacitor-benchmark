import { Network } from '@capacitor/network';

const statusEl = document.getElementById('net-status') as HTMLSpanElement;

function setStatus(connected: boolean): void {
  statusEl.textContent = connected ? 'online' : 'offline';
}

// Subscribe to live connectivity changes
Network.addListener('networkStatusChange', (status) => {
  setStatus(status.connected);
});

// Set initial status on page load
Network.getStatus().then((status) => {
  setStatus(status.connected);
});
