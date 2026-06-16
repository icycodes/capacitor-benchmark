import { Clipboard } from '@capacitor/clipboard';

const clipInput = document.getElementById('clip-input') as HTMLInputElement | null;
const clipWriteBtn = document.getElementById('clip-write-btn') as HTMLButtonElement | null;
const clipReadBtn = document.getElementById('clip-read-btn') as HTMLButtonElement | null;
const clipOutput = document.getElementById('clip-output') as HTMLSpanElement | null;

if (clipWriteBtn && clipInput) {
  clipWriteBtn.addEventListener('click', async () => {
    const textToCopy = clipInput.value;
    await Clipboard.write({
      string: textToCopy
    });
  });
}

if (clipReadBtn && clipOutput) {
  clipReadBtn.addEventListener('click', async () => {
    const { value } = await Clipboard.read();
    clipOutput.textContent = value;
  });
}
