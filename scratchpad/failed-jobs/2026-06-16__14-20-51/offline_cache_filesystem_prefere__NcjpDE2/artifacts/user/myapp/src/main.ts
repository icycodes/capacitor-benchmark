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

async function updateMetaDisplay() {
  const { value } = await Preferences.get({ key: 'cache_meta:demo' });
  if (value) {
    try {
      const meta = JSON.parse(value);
      metaEtagEl.textContent = meta.etag || '';
      metaFetchedAtEl.textContent = meta.fetchedAt ? meta.fetchedAt.toString() : '';
    } catch (e) {
      metaEtagEl.textContent = '';
      metaFetchedAtEl.textContent = '';
    }
  } else {
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
}

fetchButton.addEventListener('click', async () => {
  statusEl.textContent = 'fetching';
  try {
    const url = urlInput.value;
    const result = await getCached('demo', url);
    statusEl.textContent = 'success';
    dataEl.textContent = JSON.stringify(result.data);
    sourceEl.textContent = result.source;
    await updateMetaDisplay();
  } catch (err: any) {
    statusEl.textContent = `error: ${err.message}`;
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
  } catch (err: any) {
    statusEl.textContent = `error: ${err.message}`;
  }
});

// Initial load
updateMetaDisplay();
