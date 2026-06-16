import { Preferences } from '@capacitor/preferences';

const keyInput = document.getElementById('kv-key') as HTMLInputElement;
const valueInput = document.getElementById('kv-value') as HTMLInputElement;
const setBtn = document.getElementById('kv-set-btn') as HTMLButtonElement;
const removeBtn = document.getElementById('kv-remove-btn') as HTMLButtonElement;
const clearBtn = document.getElementById('kv-clear-btn') as HTMLButtonElement;
const kvList = document.getElementById('kv-list') as HTMLUListElement;

async function refreshList(): Promise<void> {
  // Clear existing list items
  kvList.innerHTML = '';

  // Enumerate all stored keys
  const { keys } = await Preferences.keys();
  const keyNames = keys.map((k) => k);

  // Fetch each key's value and render
  for (const key of keyNames) {
    const { value } = await Preferences.get({ key });
    const li = document.createElement('li');
    li.setAttribute('data-key', key);
    li.textContent = `${key}=${value ?? ''}`;
    kvList.appendChild(li);
  }
}

setBtn.addEventListener('click', async () => {
  const key = keyInput.value.trim();
  const value = valueInput.value;
  if (!key) return;
  await Preferences.set({ key, value });
  await refreshList();
});

removeBtn.addEventListener('click', async () => {
  const key = keyInput.value.trim();
  if (!key) return;
  await Preferences.remove({ key });
  await refreshList();
});

clearBtn.addEventListener('click', async () => {
  await Preferences.clear();
  await refreshList();
});

// Refresh the list on page load
refreshList();
