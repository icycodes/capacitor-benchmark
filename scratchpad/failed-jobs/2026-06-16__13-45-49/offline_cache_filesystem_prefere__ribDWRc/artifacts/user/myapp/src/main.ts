import { getCached, invalidate } from './cache/offlineCache';
import { Preferences } from '@capacitor/preferences';

const urlInput = document.getElementById('url-input') as HTMLInputElement;
const fetchButton = document.getElementById('fetch-button') as HTMLButtonElement;
const invalidateButton = document.getElementById('invalidate-button') as HTMLButtonElement;

const statusEl = document.getElementById('status') as HTMLElement;
const sourceEl = document.getElementById('source') as HTMLElement;
const dataEl = document.getElementById('data') as HTMLElement;
const metaEtagEl = document.getElementById('meta-etag') as HTMLElement;
const metaFetchedAtEl = document.getElementById('meta-fetched-at') as HTMLElement;

async function updateMetadata() {
  try {
    const metaResult = await Preferences.get({ key: 'cache_meta:demo' });
    if (metaResult.value) {
      const meta = JSON.parse(metaResult.value);
      metaEtagEl.textContent = meta.etag !== undefined ? String(meta.etag) : '';
      metaFetchedAtEl.textContent = meta.fetchedAt !== undefined ? String(meta.fetchedAt) : '';
    } else {
      metaEtagEl.textContent = '';
      metaFetchedAtEl.textContent = '';
    }
  } catch (err) {
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
}

fetchButton.addEventListener('click', async () => {
  statusEl.textContent = 'fetching';
  
  // Clear other fields while fetching? Wait, the requirement says "while a getCached call is in flight" `#status` is `fetching`.
  // Let's clear or keep them? To be safe, let's keep them or clear them. Actually, "renders the result" is after success.
  // Wait, let's keep them or clear them. Let's make sure we don't clear them if we are doing a second fetch, but wait:
  // "clicking #fetch-button again must end with #status equal to success, #source equal to cache, #data still equal to the same JSON body, and #meta-etag unchanged."
  // So during fetching, we can leave other elements as they are, and update them on success/error.
  
  try {
    const url = urlInput.value.trim();
    const result = await getCached('demo', url);
    
    statusEl.textContent = 'success';
    sourceEl.textContent = result.source;
    dataEl.textContent = JSON.stringify(result.data);
    
    await updateMetadata();
  } catch (err: any) {
    statusEl.textContent = `error: ${err.message || err}`;
    sourceEl.textContent = '';
    dataEl.textContent = '';
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  }
});

invalidateButton.addEventListener('click', async () => {
  try {
    await invalidate('demo');
    
    statusEl.textContent = 'invalidated';
    sourceEl.textContent = '';
    dataEl.textContent = '';
    metaEtagEl.textContent = '';
    metaFetchedAtEl.textContent = '';
  } catch (err: any) {
    statusEl.textContent = `error: ${err.message || err}`;
  }
});
