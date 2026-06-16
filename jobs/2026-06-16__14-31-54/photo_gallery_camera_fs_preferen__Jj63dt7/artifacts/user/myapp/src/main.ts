import { capturePhoto, listPhotos, deletePhoto } from './gallery';

const gallery = { capturePhoto, listPhotos, deletePhoto };
(window as any).gallery = gallery;

const captureBtn = document.getElementById('capture-btn') as HTMLButtonElement;
const captureStatus = document.getElementById('capture-status') as HTMLSpanElement;

captureBtn.addEventListener('click', async () => {
  captureStatus.textContent = 'capturing';
  try {
    const path = await gallery.capturePhoto();
    captureStatus.textContent = 'saved';
  } catch (err: any) {
    captureStatus.textContent = `error: ${err.message || err}`;
  }
});