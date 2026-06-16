import { CapacitorHttp, type HttpResponse } from '@capacitor/core';
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

interface CacheMeta {
  etag: string;
  fetchedAt: number;
}

function getEtagHeader(headers: Record<string, string>): string | undefined {
  // Headers may come with various casing; look up case-insensitively
  const keys = Object.keys(headers);
  const etagKey = keys.find((k) => k.toLowerCase() === 'etag');
  return etagKey ? headers[etagKey] : undefined;
}

export async function getCached(
  key: string,
  url: string
): Promise<{ data: unknown; source: 'network' | 'cache' }> {
  const metaKey = `cache_meta:${key}`;
  const filePath = `cache/${key}.json`;

  // Check for existing metadata
  const { value: metaRaw } = await Preferences.get({ key: metaKey });

  if (!metaRaw) {
    // First call – no metadata yet, fetch fresh
    const response: HttpResponse = await CapacitorHttp.get({ url });
    const etag = getEtagHeader(response.headers) || '';
    const data = response.data;

    // Persist the response body to disk
    await Filesystem.writeFile({
      path: filePath,
      data: JSON.stringify(data),
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
      recursive: true,
    });

    // Persist metadata
    await Preferences.set({
      key: metaKey,
      value: JSON.stringify({ etag, fetchedAt: Date.now() }),
    });

    return { data, source: 'network' };
  }

  // Subsequent call – we have metadata, send conditional request
  const meta: CacheMeta = JSON.parse(metaRaw);

  const response: HttpResponse = await CapacitorHttp.get({
    url,
    headers: { 'If-None-Match': meta.etag },
  });

  if (response.status === 304) {
    // Not Modified – read from cache
    const fileResult = await Filesystem.readFile({
      path: filePath,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });
    const data = JSON.parse(fileResult.data as string);

    // Refresh only the fetchedAt timestamp
    await Preferences.set({
      key: metaKey,
      value: JSON.stringify({ etag: meta.etag, fetchedAt: Date.now() }),
    });

    return { data, source: 'cache' };
  }

  // 200 OK with new content
  const newEtag = getEtagHeader(response.headers) || '';
  const data = response.data;

  // Overwrite the on-disk file
  await Filesystem.writeFile({
    path: filePath,
    data: JSON.stringify(data),
    directory: Directory.Cache,
    encoding: Encoding.UTF8,
    recursive: true,
  });

  // Update both etag and fetchedAt
  await Preferences.set({
    key: metaKey,
    value: JSON.stringify({ etag: newEtag, fetchedAt: Date.now() }),
  });

  return { data, source: 'network' };
}

export async function invalidate(key: string): Promise<void> {
  const metaKey = `cache_meta:${key}`;
  const filePath = `cache/${key}.json`;

  // Remove metadata – silently ignore if missing
  try {
    await Preferences.remove({ key: metaKey });
  } catch {
    // Missing metadata must not throw
  }

  // Remove on-disk file – silently ignore if missing
  try {
    await Filesystem.deleteFile({
      path: filePath,
      directory: Directory.Cache,
    });
  } catch {
    // Missing file must not throw
  }
}