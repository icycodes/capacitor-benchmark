import { getCached, invalidate } from './cache/offlineCache';
import { Preferences } from '@capacitor/preferences';

const urlInput = document.getElementById('url-input') as HTMLInputElement;
const fetchButton = document.getElementById('fetch-button') as HTMLButtonElement;
const invalidateButton = document.getElementById('invalidate-button') as HTMLButtonElement;
const statusEl = document.getElementById('status')!;
const dataEl = document.getElementById('data')!;
const sourceEl = document.getElementById('source')!;
const metaEtagEl = document.getElementById('meta-etag')!;
const metaFetchedAtEl = document.getElementById('meta-fetched-at')!;

function clearDisplay(): void {
  dataEl.textContent = '';
  sourceEl.textContent = '';
  metaEtagEl.textContent = '';
  metaFetchedAtEl.textContent = '';
}

async function refreshMetaDisplay(): Promise<void> {
  try {
    const result = await Preferences.get({ key: 'cache_meta:demo' });
    if (result.value !== null && result.value !== undefined) {
      const meta = JSON.parse(result.value);
      metaEtagEl.textContent = meta.etag || '';
      metaFetchedAtEl.textContent = String(meta.fetchedAt || '');
    } else {
      metaEtagEl.textContent = '';
      metaFetchedAtEl.textContent = '';
    }
  } catch {
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
}

fetchButton.addEventListener('click', async () => {
  statusEl.textContent = 'fetching';
  try {
    const result = await getCached('demo', urlInput.value);
    statusEl.textContent = 'success';
    dataEl.textContent = JSON.stringify(result.data);
    sourceEl.textContent = result.source;
    await refreshMetaDisplay();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    statusEl.textContent = `error: ${message}`;
    clearDisplay();
  }
});

invalidateButton.addEventListener('click', async () => {
  try {
    await invalidate('demo');
    statusEl.textContent = 'invalidated';
    clearDisplay();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    statusEl.textContent = `error: ${message}`;
  }
});
