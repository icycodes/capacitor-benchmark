import { getCached, invalidate } from './cache/offlineCache';
import { Preferences } from '@capacitor/preferences';

const urlInput = document.getElementById('url-input') as HTMLInputElement;
const fetchButton = document.getElementById('fetch-button') as HTMLButtonElement;
const invalidateButton = document.getElementById('invalidate-button') as HTMLButtonElement;
const statusEl = document.getElementById('status') as HTMLElement;
const dataEl = document.getElementById('data') as HTMLElement;
const sourceEl = document.getElementById('source') as HTMLElement;
const metaEtagEl = document.getElementById('meta-etag') as HTMLElement;
const metaFetchedAtEl = document.getElementById('meta-fetched-at') as HTMLElement;

async function refreshMeta(): Promise<void> {
  const { value } = await Preferences.get({ key: 'cache_meta:demo' });
  if (value) {
    try {
      const meta = JSON.parse(value) as { etag: string; fetchedAt: number };
      metaEtagEl.textContent = meta.etag;
      metaFetchedAtEl.textContent = String(meta.fetchedAt);
    } catch {
      metaEtagEl.textContent = '';
      metaFetchedAtEl.textContent = '';
    }
  } else {
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
}

fetchButton.addEventListener('click', async () => {
  const url = urlInput.value;
  statusEl.textContent = 'fetching';
  dataEl.textContent = '';
  sourceEl.textContent = '';

  try {
    const result = await getCached('demo', url);
    statusEl.textContent = 'success';
    dataEl.textContent = JSON.stringify(result.data);
    sourceEl.textContent = result.source;
    await refreshMeta();
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    statusEl.textContent = `error: ${message}`;
    dataEl.textContent = '';
    sourceEl.textContent = '';
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
});

invalidateButton.addEventListener('click', async () => {
  try {
    await invalidate('demo');
    statusEl.textContent = 'invalidated';
    dataEl.textContent = '';
    sourceEl.textContent = '';
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    statusEl.textContent = `error: ${message}`;
  }
});
