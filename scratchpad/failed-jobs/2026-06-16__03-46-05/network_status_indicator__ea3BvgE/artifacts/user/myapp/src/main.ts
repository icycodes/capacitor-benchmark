import { Network } from '@capacitor/network';

const statusEl = document.getElementById('net-status') as HTMLSpanElement | null;

async function updateStatus(): Promise<void> {
  const status = await Network.getStatus();
  if (statusEl) {
    statusEl.textContent = status.connected ? 'online' : 'offline';
  }
}

Network.addListener('networkStatusChange', (status) => {
  if (statusEl) {
    statusEl.textContent = status.connected ? 'online' : 'offline';
  }
});

updateStatus();
