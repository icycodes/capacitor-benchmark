import { CapacitorCookies, CapacitorHttp } from '@capacitor/core';

function getApiBaseUrl(): string {
  const env = (typeof process !== 'undefined' && process.env) ? process.env : {};
  const meta = (import.meta as any).env || {};
  return (env.API_BASE_URL || meta.API_BASE_URL || '').trim();
}

function getUrl(path: string): string {
  const base = getApiBaseUrl();
  const cleanBase = base.endsWith('/') ? base.slice(0, -1) : base;
  return `${cleanBase}${path}`;
}

function getHeaderCaseInsensitive(headers: Record<string, string> | undefined, name: string): string | undefined {
  if (!headers) return undefined;
  const lowerName = name.toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === lowerName) {
      return headers[key];
    }
  }
  return undefined;
}

export async function login(user: string, pass: string): Promise<boolean> {
  try {
    const url = getUrl('/login');
    const response = await CapacitorHttp.post({
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      data: { user, pass },
    });

    if (response.status >= 200 && response.status < 300) {
      let sessionId: string | undefined;

      if (response.data && typeof response.data === 'object') {
        sessionId = response.data.session_id;
      } else if (response.data && typeof response.data === 'string') {
        try {
          const parsed = JSON.parse(response.data);
          if (parsed && typeof parsed === 'object') {
            sessionId = parsed.session_id;
          }
        } catch {
          // ignore
        }
      }

      if (!sessionId && response.headers) {
        const setCookieHeader = getHeaderCaseInsensitive(response.headers, 'set-cookie');
        if (setCookieHeader) {
          const match = setCookieHeader.match(/session_id=([^;]+)/);
          if (match) {
            sessionId = match[1];
          }
        }
      }

      if (sessionId) {
        await CapacitorCookies.setCookie({
          url: getApiBaseUrl(),
          key: 'session_id',
          value: sessionId,
        });
      }

      return true;
    }

    return false;
  } catch (error) {
    return false;
  }
}

export async function whoami(): Promise<string | null> {
  try {
    const url = getUrl('/whoami');
    const response = await CapacitorHttp.get({
      url,
    });

    if (response.status >= 200 && response.status < 300) {
      let dataObj: any = null;
      if (response.data && typeof response.data === 'object') {
        dataObj = response.data;
      } else if (response.data && typeof response.data === 'string') {
        try {
          dataObj = JSON.parse(response.data);
        } catch {
          // ignore
        }
      }

      if (dataObj && typeof dataObj === 'object' && typeof dataObj.user === 'string') {
        return dataObj.user;
      }
    }
    return null;
  } catch (error) {
    return null;
  }
}

export async function logout(): Promise<void> {
  await CapacitorCookies.clearAllCookies();
}
