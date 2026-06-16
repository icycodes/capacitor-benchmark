import { Clipboard } from '@capacitor/clipboard';

const inputEl = document.getElementById('clip-input') as HTMLInputElement;
const writeBtn = document.getElementById('clip-write-btn') as HTMLButtonElement;
const readBtn = document.getElementById('clip-read-btn') as HTMLButtonElement;
const outputEl = document.getElementById('clip-output') as HTMLSpanElement;

writeBtn.addEventListener('click', async () => {
  await Clipboard.write({ string: inputEl.value });
});

readBtn.addEventListener('click', async () => {
  const result = await Clipboard.read();
  outputEl.textContent = result.value;
});