import { CapacitorCookies, CapacitorHttp } from '@capacitor/core';

const API_BASE_URL: string = process.env.API_BASE_URL ?? '';

export async function login(user: string, pass: string): Promise<boolean> {
  const response = await CapacitorHttp.post({
    url: `${API_BASE_URL}/login`,
    headers: { 'Content-Type': 'application/json' },
    data: { user, pass },
  });

  if (response.status >= 200 && response.status < 300) {
    const sessionId: string | undefined =
      response.data?.session_id;

    if (sessionId) {
      await CapacitorCookies.setCookie({
        url: API_BASE_URL,
        key: 'session_id',
        value: sessionId,
      });
    } else {
      // Fallback: try to extract session_id from Set-Cookie header
      const setCookieHeader: string | undefined =
        response.headers?.['set-cookie'] ?? response.headers?.['Set-Cookie'];
      if (setCookieHeader) {
        const match = setCookieHeader.match(/session_id=([^;]+)/);
        if (match?.[1]) {
          await CapacitorCookies.setCookie({
            url: API_BASE_URL,
            key: 'session_id',
            value: match[1],
          });
        }
      }
    }

    return true;
  }

  return false;
}

export async function whoami(): Promise<string | null> {
  const response = await CapacitorHttp.get({
    url: `${API_BASE_URL}/whoami`,
  });

  if (response.status >= 200 && response.status < 300) {
    return response.data?.user ?? null;
  }

  return null;
}

export async function logout(): Promise<void> {
  await CapacitorCookies.clearAllCookies();
}