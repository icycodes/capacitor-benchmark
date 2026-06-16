import { capturePhoto, listPhotos, deletePhoto } from "./gallery";

// Expose gallery functions on window for automated tests
(window as any).gallery = {
  capturePhoto,
  listPhotos,
  deletePhoto,
};

// Wire up the capture button
const captureBtn = document.getElementById("capture-btn");
const captureStatus = document.getElementById("capture-status");

if (captureBtn && captureStatus) {
  captureBtn.addEventListener("click", async () => {
    captureStatus.textContent = "capturing";
    try {
      await capturePhoto();
      captureStatus.textContent = "saved";
    } catch (err: any) {
      captureStatus.textContent = `error: ${err.message ?? String(err)}`;
    }
  });
}
