import { Camera } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

const PHOTO_INDEX_KEY = 'photo_index';

export async function capturePhoto(): Promise<string> {
  const result = await Camera.takePhoto({
    saveToGallery: false,
    includeMetadata: true
  });

  const base64Data = (result as any).thumbnail || result.base64String;
  if (!base64Data) {
    throw new Error('No image data returned from camera');
  }

  const isoTimestamp = new Date().toISOString();
  const path = `photos/${isoTimestamp}.jpeg`;

  await Filesystem.writeFile({
    path,
    data: base64Data,
    directory: Directory.Data,
    recursive: true
  });

  const photos = await listPhotos();
  photos.push(path);
  await Preferences.set({
    key: PHOTO_INDEX_KEY,
    value: JSON.stringify(photos)
  });

  return path;
}

export async function listPhotos(): Promise<string[]> {
  const { value } = await Preferences.get({ key: PHOTO_INDEX_KEY });
  if (value === null) {
    return [];
  }
  return JSON.parse(value);
}

export async function deletePhoto(path: string): Promise<void> {
  try {
    await Filesystem.deleteFile({
      path,
      directory: Directory.Data
    });
  } catch (e) {
    // Ignore error if file does not exist
  }

  const photos = await listPhotos();
  await Preferences.set({
    key: PHOTO_INDEX_KEY,
    value: JSON.stringify(photos.filter(p => p !== path))
  });
}
