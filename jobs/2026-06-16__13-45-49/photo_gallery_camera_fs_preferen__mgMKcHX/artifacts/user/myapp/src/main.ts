import { capturePhoto, listPhotos, deletePhoto } from './gallery';

declare global {
  interface Window {
    gallery: {
      capturePhoto: () => Promise<string>;
      listPhotos: () => Promise<string[]>;
      deletePhoto: (path: string) => Promise<void>;
    };
  }
}

window.gallery = {
  capturePhoto,
  listPhotos,
  deletePhoto,
};

const btn = document.getElementById('capture-btn');
const status = document.getElementById('capture-status');

if (btn && status) {
  btn.addEventListener('click', async () => {
    status.textContent = 'capturing';
    try {
      await window.gallery.capturePhoto();
      status.textContent = 'saved';
    } catch (e: any) {
      status.textContent = `error: ${e.message || e}`;
    }
  });
}
