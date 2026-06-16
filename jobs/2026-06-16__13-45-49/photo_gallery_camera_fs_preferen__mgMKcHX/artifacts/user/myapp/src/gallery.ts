import { Camera } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

const PHOTO_INDEX_KEY = 'photo_index';

export async function capturePhoto(): Promise<string> {
  const isoTimestamp = new Date().toISOString();
  const path = `photos/${isoTimestamp}.jpeg`;

  // Take photo
  const result = await Camera.takePhoto({
    saveToGallery: false,
    includeMetadata: true,
  });

  const base64Data = result.thumbnail;
  if (!base64Data) {
    throw new Error('No image data returned from camera');
  }

  // Write file
  await Filesystem.writeFile({
    path,
    data: base64Data,
    directory: Directory.Data,
    recursive: true,
  });

  // Update preferences index
  const currentPhotos = await listPhotos();
  currentPhotos.push(path);
  await Preferences.set({
    key: PHOTO_INDEX_KEY,
    value: JSON.stringify(currentPhotos),
  });

  return path;
}

export async function listPhotos(): Promise<string[]> {
  const { value } = await Preferences.get({ key: PHOTO_INDEX_KEY });
  if (value === null) {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed;
    }
  } catch (e) {
    console.error('Failed to parse photo index:', e);
  }
  return [];
}

export async function deletePhoto(path: string): Promise<void> {
  // side-effect 1: delete file (must occur, but if file does not exist, the index must still be updated)
  try {
    await Filesystem.deleteFile({
      path,
      directory: Directory.Data,
    });
  } catch (e) {
    console.warn(`Failed to delete file at ${path}:`, e);
  }

  // side-effect 2: update index
  const currentPhotos = await listPhotos();
  const updatedPhotos = currentPhotos.filter((p) => p !== path);
  await Preferences.set({
    key: PHOTO_INDEX_KEY,
    value: JSON.stringify(updatedPhotos),
  });
}
