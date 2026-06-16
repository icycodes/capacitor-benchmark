import { Clipboard } from '@capacitor/clipboard';

const input = document.getElementById('clip-input') as HTMLInputElement;
const writeBtn = document.getElementById('clip-write-btn') as HTMLButtonElement;
const readBtn = document.getElementById('clip-read-btn') as HTMLButtonElement;
const output = document.getElementById('clip-output') as HTMLSpanElement;

writeBtn.addEventListener('click', async () => {
  if (input) {
    await Clipboard.write({
      string: input.value
    });
  }
});

readBtn.addEventListener('click', async () => {
  const result = await Clipboard.read();
  if (output) {
    output.textContent = result.value;
  }
});
