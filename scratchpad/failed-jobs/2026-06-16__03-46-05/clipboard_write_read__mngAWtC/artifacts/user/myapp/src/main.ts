import { Clipboard } from '@capacitor/clipboard';

const clipInput = document.getElementById('clip-input') as HTMLInputElement;
const writeBtn = document.getElementById('clip-write-btn') as HTMLButtonElement;
const readBtn = document.getElementById('clip-read-btn') as HTMLButtonElement;
const clipOutput = document.getElementById('clip-output') as HTMLSpanElement;

writeBtn.addEventListener('click', async () => {
  const value = clipInput.value;
  await Clipboard.write({ string: value });
});

readBtn.addEventListener('click', async () => {
  const result = await Clipboard.read();
  clipOutput.textContent = result.value;
});
