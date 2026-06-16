import { Camera, CameraResultType } from "@capacitor/camera";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Preferences } from "@capacitor/preferences";

const INDEX_KEY = "photo_index";

async function readIndex(): Promise<string[]> {
  const { value } = await Preferences.get({ key: INDEX_KEY });
  if (value === null) {
    return [];
  }
  return JSON.parse(value) as string[];
}

async function writeIndex(paths: string[]): Promise<void> {
  await Preferences.set({ key: INDEX_KEY, value: JSON.stringify(paths) });
}

export async function capturePhoto(): Promise<string> {
  const result = await Camera.takePhoto({
    resultType: CameraResultType.Base64,
    saveToGallery: false,
    includeMetadata: true,
  });

  const base64Data = result.thumbnail!;
  const timestamp = new Date().toISOString();
  const path = `photos/${timestamp}.jpeg`;

  await Filesystem.writeFile({
    path,
    data: base64Data,
    directory: Directory.Data,
    recursive: true,
  });

  const index = await readIndex();
  index.push(path);
  await writeIndex(index);

  return path;
}

export async function listPhotos(): Promise<string[]> {
  return readIndex();
}

export async function deletePhoto(path: string): Promise<void> {
  try {
    await Filesystem.deleteFile({
      path,
      directory: Directory.Data,
    });
  } catch {
    // File may not exist — still update the index
  }

  const index = await readIndex();
  const filtered = index.filter((p) => p !== path);
  await writeIndex(filtered);
}
