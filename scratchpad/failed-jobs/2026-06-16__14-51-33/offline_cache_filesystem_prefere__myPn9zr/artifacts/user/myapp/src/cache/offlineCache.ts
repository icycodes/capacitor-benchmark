import { CapacitorHttp } from '@capacitor/core';
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

interface CacheMeta {
  etag: string;
  fetchedAt: number;
}

function getMetaKey(key: string): string {
  return `cache_meta:${key}`;
}

function getFilePath(key: string): string {
  return `cache/${key}.json`;
}

function findHeaderCaseInsensitive(
  headers: Record<string, string>,
  target: string
): string | undefined {
  const lower = target.toLowerCase();
  for (const h of Object.keys(headers)) {
    if (h.toLowerCase() === lower) {
      return headers[h];
    }
  }
  return undefined;
}

async function readMeta(key: string): Promise<CacheMeta | null> {
  const result = await Preferences.get({ key: getMetaKey(key) });
  if (result.value === null || result.value === undefined) {
    return null;
  }
  return JSON.parse(result.value) as CacheMeta;
}

async function writeMeta(key: string, meta: CacheMeta): Promise<void> {
  await Preferences.set({
    key: getMetaKey(key),
    value: JSON.stringify(meta),
  });
}

export async function getCached(
  key: string,
  url: string
): Promise<{ data: unknown; source: 'network' | 'cache' }> {
  const meta = await readMeta(key);

  const requestHeaders: Record<string, string> = {};
  if (meta) {
    requestHeaders['If-None-Match'] = meta.etag;
  }

  const response = await CapacitorHttp.get({
    url,
    headers: requestHeaders,
  });

  // 304 Not Modified — return cached data
  if (response.status === 304) {
    const fileResult = await Filesystem.readFile({
      path: getFilePath(key),
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });
    const data = JSON.parse(fileResult.data as string);
    // Refresh fetchedAt timestamp only, keep etag unchanged
    await writeMeta(key, { etag: meta!.etag, fetchedAt: Date.now() });
    return { data, source: 'cache' };
  }

  // 200 OK (first fetch or changed content)
  const data: unknown = response.data;
  const etag = findHeaderCaseInsensitive(response.headers, 'ETag') || '';

  // Persist the response body to disk
  const payload = JSON.stringify(data);
  await Filesystem.writeFile({
    path: getFilePath(key),
    data: payload,
    directory: Directory.Cache,
    encoding: Encoding.UTF8,
    recursive: true,
  });

  // Persist metadata
  const newMeta: CacheMeta = { etag, fetchedAt: Date.now() };
  await writeMeta(key, newMeta);

  return { data, source: 'network' };
}

export async function invalidate(key: string): Promise<void> {
  // Remove metadata — ignore if it doesn't exist
  try {
    await Preferences.remove({ key: getMetaKey(key) });
  } catch {
    // Ignore missing metadata
  }

  // Remove cached file — ignore if it doesn't exist
  try {
    await Filesystem.deleteFile({
      path: getFilePath(key),
      directory: Directory.Cache,
    });
  } catch {
    // Ignore missing file
  }
}
