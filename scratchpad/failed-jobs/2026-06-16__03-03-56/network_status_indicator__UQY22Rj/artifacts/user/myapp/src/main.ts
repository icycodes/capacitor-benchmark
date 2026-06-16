import { Network } from '@capacitor/network';

async function initNetworkStatus() {
  const statusEl = document.getElementById('net-status');
  if (!statusEl) {
    console.error('Element #net-status not found');
    return;
  }

  // Update element text content based on connection status
  const updateStatus = (connected: boolean) => {
    statusEl.textContent = connected ? 'online' : 'offline';
  };

  // Subscribe to live connectivity updates
  await Network.addListener('networkStatusChange', (status) => {
    updateStatus(status.connected);
  });

  // Query the current network status on page load
  try {
    const status = await Network.getStatus();
    updateStatus(status.connected);
  } catch (err) {
    console.error('Failed to get network status:', err);
  }
}

// Run immediately or when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNetworkStatus);
} else {
  initNetworkStatus();
}
