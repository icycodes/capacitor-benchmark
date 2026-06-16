import { capturePhoto, listPhotos, deletePhoto } from './gallery';

// Expose gallery API on window so automated tests can invoke it
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

// Render the UI
const app = document.getElementById('app');
if (app) {
  app.innerHTML = `
    <h1>Photo Gallery</h1>
    <button id="capture-btn" type="button">Capture Photo</button>
    <p id="capture-status">idle</p>
    <ul id="photo-list"></ul>
  `;

  const captureBtn = document.getElementById('capture-btn') as HTMLButtonElement;
  const captureStatus = document.getElementById('capture-status') as HTMLParagraphElement;

  captureBtn.addEventListener('click', async () => {
    captureStatus.textContent = 'capturing';
    try {
      const path = await capturePhoto();
      captureStatus.textContent = 'saved';
      console.log('Photo saved at:', path);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      captureStatus.textContent = `error: ${message}`;
      console.error('Capture failed:', err);
    }
  });
}
