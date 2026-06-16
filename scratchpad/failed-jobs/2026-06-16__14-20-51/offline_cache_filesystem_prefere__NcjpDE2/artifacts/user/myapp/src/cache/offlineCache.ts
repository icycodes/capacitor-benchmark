import { CapacitorHttp } from '@capacitor/core';
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

export async function getCached(key: string, url: string): Promise<{ data: unknown; source: 'network' | 'cache' }> {
  const metaKey = `cache_meta:${key}`;
  const filePath = `cache/${key}.json`;

  const { value: metaStr } = await Preferences.get({ key: metaKey });
  let etag: string | undefined;

  if (metaStr) {
    try {
      const meta = JSON.parse(metaStr);
      etag = meta.etag;
    } catch (e) {
      // ignore
    }
  }

  const headers: Record<string, string> = {};
  if (etag) {
    headers['If-None-Match'] = etag;
  }

  const response = await CapacitorHttp.get({ url, headers });

  if (response.status === 304 && etag) {
    // Read from cache
    const { data: fileData } = await Filesystem.readFile({
      path: filePath,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });

    const parsedData = JSON.parse(fileData as string);

    // Update fetchedAt
    const newMeta = { etag, fetchedAt: Date.now() };
    await Preferences.set({ key: metaKey, value: JSON.stringify(newMeta) });

    return { data: parsedData, source: 'cache' };
  }

  // Network success
  // Find ETag case-insensitively
  let newEtag: string | undefined;
  for (const k in response.headers) {
    if (k.toLowerCase() === 'etag') {
      newEtag = response.headers[k];
      break;
    }
  }

  const data = response.data; // CapacitorHttp parses JSON if Content-Type is application/json

  // Persist body
  await Filesystem.writeFile({
    path: filePath,
    directory: Directory.Cache,
    encoding: Encoding.UTF8,
    data: JSON.stringify(data),
    recursive: true,
  });

  // Persist meta
  const newMeta = { etag: newEtag, fetchedAt: Date.now() };
  await Preferences.set({ key: metaKey, value: JSON.stringify(newMeta) });

  return { data, source: 'network' };
}

export async function invalidate(key: string): Promise<void> {
  const metaKey = `cache_meta:${key}`;
  const filePath = `cache/${key}.json`;

  await Preferences.remove({ key: metaKey });
  try {
    await Filesystem.deleteFile({
      path: filePath,
      directory: Directory.Cache,
    });
  } catch (e) {
    // Ignore missing file
  }
}
