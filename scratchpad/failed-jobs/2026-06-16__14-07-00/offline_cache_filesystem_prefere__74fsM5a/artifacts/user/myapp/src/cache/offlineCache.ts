import { CapacitorHttp } from '@capacitor/core';
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

interface CacheMeta {
  etag: string;
  fetchedAt: number;
}

function metaKey(key: string): string {
  return `cache_meta:${key}`;
}

function filePath(key: string): string {
  return `cache/${key}.json`;
}

async function getStoredMeta(key: string): Promise<CacheMeta | null> {
  const { value } = await Preferences.get({ key: metaKey(key) });
  if (!value) return null;
  try {
    return JSON.parse(value) as CacheMeta;
  } catch {
    return null;
  }
}

async function saveMeta(key: string, meta: CacheMeta): Promise<void> {
  await Preferences.set({
    key: metaKey(key),
    value: JSON.stringify(meta),
  });
}

function getEtag(headers: Record<string, string>): string {
  // Case-insensitive header lookup
  for (const [k, v] of Object.entries(headers)) {
    if (k.toLowerCase() === 'etag') {
      return v;
    }
  }
  return '';
}

export async function getCached(
  key: string,
  url: string
): Promise<{ data: unknown; source: 'network' | 'cache' }> {
  const meta = await getStoredMeta(key);

  if (!meta) {
    // First call: no metadata, do a fresh GET
    const response = await CapacitorHttp.get({ url });
    const etag = getEtag(response.headers as Record<string, string>);
    const data: unknown = response.data;
    const serialized = JSON.stringify(data);

    await Filesystem.writeFile({
      path: filePath(key),
      data: serialized,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
      recursive: true,
    });

    await saveMeta(key, { etag, fetchedAt: Date.now() });

    return { data, source: 'network' };
  }

  // Subsequent call: send conditional request with If-None-Match
  const response = await CapacitorHttp.get({
    url,
    headers: { 'If-None-Match': meta.etag },
  });

  if (response.status === 304) {
    // Not modified — read from cache
    const fileResult = await Filesystem.readFile({
      path: filePath(key),
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });
    const data: unknown = JSON.parse(fileResult.data as string);

    // Refresh only fetchedAt, keep etag unchanged
    await saveMeta(key, { etag: meta.etag, fetchedAt: Date.now() });

    return { data, source: 'cache' };
  }

  // 200 OK with potentially new ETag
  const newEtag = getEtag(response.headers as Record<string, string>);
  const data: unknown = response.data;
  const serialized = JSON.stringify(data);

  await Filesystem.writeFile({
    path: filePath(key),
    data: serialized,
    directory: Directory.Cache,
    encoding: Encoding.UTF8,
    recursive: true,
  });

  await saveMeta(key, { etag: newEtag, fetchedAt: Date.now() });

  return { data, source: 'network' };
}

export async function invalidate(key: string): Promise<void> {
  // Remove on-disk file — ignore errors if missing
  try {
    await Filesystem.deleteFile({
      path: filePath(key),
      directory: Directory.Cache,
    });
  } catch {
    // File may not exist; that's fine
  }

  // Remove metadata — ignore errors if missing
  try {
    await Preferences.remove({ key: metaKey(key) });
  } catch {
    // Key may not exist; that's fine
  }
}
