import { getCached, invalidate } from './cache/offlineCache';
import { Preferences } from '@capacitor/preferences';

const urlInput = document.getElementById('url-input') as HTMLInputElement;
const fetchButton = document.getElementById('fetch-button') as HTMLButtonElement;
const invalidateButton = document.getElementById('invalidate-button') as HTMLButtonElement;
const statusEl = document.getElementById('status') as HTMLSpanElement;
const dataEl = document.getElementById('data') as HTMLSpanElement;
const sourceEl = document.getElementById('source') as HTMLSpanElement;
const metaEtagEl = document.getElementById('meta-etag') as HTMLSpanElement;
const metaFetchedAtEl = document.getElementById('meta-fetched-at') as HTMLSpanElement;

async function refreshMeta(): Promise<void> {
  const { value: metaRaw } = await Preferences.get({ key: 'cache_meta:demo' });
  if (metaRaw) {
    const meta = JSON.parse(metaRaw);
    metaEtagEl.textContent = meta.etag ?? '';
    metaFetchedAtEl.textContent = meta.fetchedAt != null ? String(meta.fetchedAt) : '';
  } else {
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
}

fetchButton.addEventListener('click', async () => {
  statusEl.textContent = 'fetching';
  dataEl.textContent = '';
  sourceEl.textContent = '';
  try {
    const result = await getCached('demo', urlInput.value);
    statusEl.textContent = 'success';
    dataEl.textContent = JSON.stringify(result.data);
    sourceEl.textContent = result.source;
    await refreshMeta();
  } catch (err: any) {
    statusEl.textContent = `error: ${err.message ?? err}`;
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
    statusEl.textContent = `error: ${err.message ?? err}`;
  }
});