import * as gallery from './gallery';

// Expose on window for tests
(window as any).gallery = gallery;

const captureBtn = document.getElementById('capture-btn');
const captureStatus = document.getElementById('capture-status');

if (captureBtn && captureStatus) {
  captureBtn.addEventListener('click', async () => {
    try {
      captureStatus.textContent = 'capturing';
      await gallery.capturePhoto();
      captureStatus.textContent = 'saved';
    } catch (err: any) {
      captureStatus.textContent = `error: ${err.message}`;
    }
  });
}
