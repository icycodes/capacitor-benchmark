import { Preferences } from '@capacitor/preferences';

const keyInput = document.getElementById('kv-key') as HTMLInputElement;
const valueInput = document.getElementById('kv-value') as HTMLInputElement;
const setBtn = document.getElementById('kv-set-btn') as HTMLButtonElement;
const removeBtn = document.getElementById('kv-remove-btn') as HTMLButtonElement;
const clearBtn = document.getElementById('kv-clear-btn') as HTMLButtonElement;
const kvList = document.getElementById('kv-list') as HTMLUListElement;

async function renderList(): Promise<void> {
  // Clear existing items
  while (kvList.firstChild) {
    kvList.removeChild(kvList.firstChild);
  }

  const { keys } = await Preferences.keys();

  for (const key of keys) {
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
  await renderList();
});

removeBtn.addEventListener('click', async () => {
  const key = keyInput.value.trim();
  if (!key) return;
  await Preferences.remove({ key });
  await renderList();
});

clearBtn.addEventListener('click', async () => {
  await Preferences.clear();
  await renderList();
});

// Render on page load
renderList();
