import { Network } from '@capacitor/network';

function updateStatus(connected: boolean) {
  const el = document.getElementById('net-status');
  if (el) {
    el.textContent = connected ? 'online' : 'offline';
  }
}

async function init() {
  // Query current network status on load
  const status = await Network.getStatus();
  updateStatus(status.connected);

  // Subscribe to live connectivity changes
  Network.addListener('networkStatusChange', (status) => {
    updateStatus(status.connected);
  });
}

init();