import { Camera } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

const PHOTO_INDEX_KEY = 'photo_index';

async function getIndex(): Promise<string[]> {
  const { value } = await Preferences.get({ key: PHOTO_INDEX_KEY });
  if (value === null) {
    return [];
  }
  return JSON.parse(value) as string[];
}

async function setIndex(paths: string[]): Promise<void> {
  await Preferences.set({ key: PHOTO_INDEX_KEY, value: JSON.stringify(paths) });
}

export async function capturePhoto(): Promise<string> {
  const result = await Camera.takePhoto({ saveToGallery: false, includeMetadata: true });

  const timestamp = new Date().toISOString();
  const filePath = `photos/${timestamp}.jpeg`;

  await Filesystem.writeFile({
    path: filePath,
    data: result.thumbnail,
    directory: Directory.Data,
    recursive: true,
  });

  const currentPaths = await getIndex();
  currentPaths.push(filePath);
  await setIndex(currentPaths);

  return filePath;
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

  const currentPaths = await getIndex();
  const updatedPaths = currentPaths.filter((p) => p !== path);
  await setIndex(updatedPaths);
}