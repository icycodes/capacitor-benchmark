import { CapacitorHttp } from '@capacitor/core';
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';

function getEtagHeader(headers: Record<string, string>): string | undefined {
  if (!headers) return undefined;
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === 'etag') {
      return headers[key];
    }
  }
  return undefined;
}

export async function getCached(
  key: string,
  url: string
): Promise<{ data: unknown; source: 'network' | 'cache' }> {
  const metaResult = await Preferences.get({ key: `cache_meta:${key}` });
  
  if (!metaResult.value) {
    // First call for a fresh key
    const response = await CapacitorHttp.get({ url });
    
    if (response.status !== 200) {
      throw new Error(`Failed to request from network: ${response.status}`);
    }
    
    const responseData = response.data;
    const etag = getEtagHeader(response.headers) || '';
    const dataString = typeof responseData === 'string' ? responseData : JSON.stringify(responseData);
    
    await Filesystem.writeFile({
      path: `cache/${key}.json`,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
      recursive: true,
      data: dataString,
    });
    
    const meta = { etag, fetchedAt: Date.now() };
    await Preferences.set({
      key: `cache_meta:${key}`,
      value: JSON.stringify(meta),
    });
    
    const data = typeof responseData === 'string' ? JSON.parse(dataString) : responseData;
    return { data, source: 'network' };
  } else {
    // Subsequent calls
    const meta = JSON.parse(metaResult.value);
    const response = await CapacitorHttp.get({
      url,
      headers: {
        'If-None-Match': meta.etag,
      },
    });
    
    if (response.status === 304) {
      const fileContent = await Filesystem.readFile({
        path: `cache/${key}.json`,
        directory: Directory.Cache,
        encoding: Encoding.UTF8,
      });
      
      const fileData = typeof fileContent.data === 'string' ? JSON.parse(fileContent.data) : fileContent.data;
      
      const updatedMeta = { etag: meta.etag, fetchedAt: Date.now() };
      await Preferences.set({
        key: `cache_meta:${key}`,
        value: JSON.stringify(updatedMeta),
      });
      
      return { data: fileData, source: 'cache' };
    } else if (response.status === 200) {
      const responseData = response.data;
      const etag = getEtagHeader(response.headers) || '';
      const dataString = typeof responseData === 'string' ? responseData : JSON.stringify(responseData);
      
      await Filesystem.writeFile({
        path: `cache/${key}.json`,
        directory: Directory.Cache,
        encoding: Encoding.UTF8,
        recursive: true,
        data: dataString,
      });
      
      const updatedMeta = { etag, fetchedAt: Date.now() };
      await Preferences.set({
        key: `cache_meta:${key}`,
        value: JSON.stringify(updatedMeta),
      });
      
      const data = typeof responseData === 'string' ? JSON.parse(dataString) : responseData;
      return { data, source: 'network' };
    } else {
      throw new Error(`Unexpected status code: ${response.status}`);
    }
  }
}

export async function invalidate(key: string): Promise<void> {
  try {
    await Filesystem.deleteFile({
      path: `cache/${key}.json`,
      directory: Directory.Cache,
    });
  } catch (e) {
    // Missing files must not throw
  }
  
  try {
    await Preferences.remove({
      key: `cache_meta:${key}`,
    });
  } catch (e) {
    // Missing metadata must not throw
  }
}
