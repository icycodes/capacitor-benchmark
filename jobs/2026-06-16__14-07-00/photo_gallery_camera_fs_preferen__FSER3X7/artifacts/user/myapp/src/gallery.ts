import { Camera } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

const PHOTO_INDEX_KEY = 'photo_index';

async function getIndex(): Promise<string[]> {
  const { value } = await Preferences.get({ key: PHOTO_INDEX_KEY });
  if (value === null) {
    return [];
  }
  try {
    return JSON.parse(value) as string[];
  } catch {
    return [];
  }
}

async function saveIndex(index: string[]): Promise<void> {
  await Preferences.set({ key: PHOTO_INDEX_KEY, value: JSON.stringify(index) });
}

export async function capturePhoto(): Promise<string> {
  // Camera.takePhoto is available since @capacitor/camera 8.1.0
  // On Web, result.thumbnail contains the full image as a base64 string
  const result = await Camera.takePhoto({
    saveToGallery: false,
    includeMetadata: true,
  });

  // On Web, thumbnail holds the full image base64-encoded (no data URI prefix)
  const base64Data = result.thumbnail ?? '';

  const timestamp = new Date().toISOString();
  const path = `photos/${timestamp}.jpeg`;

  await Filesystem.writeFile({
    path,
    data: base64Data,
    directory: Directory.Data,
    recursive: true,
  });

  const index = await getIndex();
  index.push(path);
  await saveIndex(index);

  return path;
}

export async function listPhotos(): Promise<string[]> {
  return getIndex();
}

export async function deletePhoto(path: string): Promise<void> {
  try {
    await Filesystem.deleteFile({
      path,
      directory: Directory.Data,
    });
  } catch {
    // File may not exist; still update the index
  }

  const index = await getIndex();
  const updated = index.filter((p) => p !== path);
  await saveIndex(updated);
}
