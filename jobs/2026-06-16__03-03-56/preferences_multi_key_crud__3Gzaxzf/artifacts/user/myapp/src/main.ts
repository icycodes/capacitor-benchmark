import { Preferences } from '@capacitor/preferences';

const keyInput = document.getElementById('kv-key') as HTMLInputElement | null;
const valueInput = document.getElementById('kv-value') as HTMLInputElement | null;
const setBtn = document.getElementById('kv-set-btn') as HTMLButtonElement | null;
const removeBtn = document.getElementById('kv-remove-btn') as HTMLButtonElement | null;
const clearBtn = document.getElementById('kv-clear-btn') as HTMLButtonElement | null;
const kvList = document.getElementById('kv-list') as HTMLUListElement | null;

async function refreshList() {
  if (!kvList) return;
  
  // Clear the existing list children
  kvList.innerHTML = '';
  
  try {
    // 1. Call Preferences.keys() to enumerate the currently stored keys
    const { keys } = await Preferences.keys();
    
    // 2. Call Preferences.get({ key }) for each key
    const pairs = await Promise.all(
      keys.map(async (key) => {
        const { value } = await Preferences.get({ key });
        return { key, value };
      })
    );
    
    // 3. Render each pair as <li data-key="<key>"><key>=<value></li> inside #kv-list
    for (const { key, value } of pairs) {
      const li = document.createElement('li');
      li.setAttribute('data-key', key);
      li.textContent = `${key}=${value !== null ? value : ''}`;
      kvList.appendChild(li);
    }
  } catch (error) {
    console.error('Error refreshing list:', error);
  }
}

// Wire up event listeners
if (setBtn) {
  setBtn.addEventListener('click', async () => {
    const key = keyInput?.value.trim() || '';
    const value = valueInput?.value || '';
    if (key) {
      await Preferences.set({ key, value });
      if (keyInput) keyInput.value = '';
      if (valueInput) valueInput.value = '';
      await refreshList();
    }
  });
}

if (removeBtn) {
  removeBtn.addEventListener('click', async () => {
    const key = keyInput?.value.trim() || '';
    if (key) {
      await Preferences.remove({ key });
      if (keyInput) keyInput.value = '';
      await refreshList();
    }
  });
}

if (clearBtn) {
  clearBtn.addEventListener('click', async () => {
    await Preferences.clear();
    await refreshList();
  });
}

// Initial load
window.addEventListener('DOMContentLoaded', refreshList);
// Also call refreshList immediately in case DOMContentLoaded has already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  refreshList();
}
