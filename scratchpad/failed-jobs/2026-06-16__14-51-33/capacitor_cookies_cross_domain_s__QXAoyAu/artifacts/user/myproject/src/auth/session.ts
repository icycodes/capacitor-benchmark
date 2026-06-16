import { CapacitorCookies, CapacitorHttp } from '@capacitor/core';

const BASE_URL: string = process.env['API_BASE_URL'] ?? '';

export async function login(user: string, pass: string): Promise<boolean> {
  const url = `${BASE_URL}/login`;

  const response = await CapacitorHttp.post({
    url,
    data: { user, pass },
    headers: { 'Content-Type': 'application/json' },
  });

  if (response.status < 200 || response.status >= 300) {
    return false;
  }

  // Extract session_id from the response body, falling back to Set-Cookie header
  let sessionId: string | undefined = response.data?.session_id;

  if (!sessionId && response.headers) {
    const setCookieHeader = response.headers['Set-Cookie'] ?? response.headers['set-cookie'];
    if (setCookieHeader) {
      const match = setCookieHeader.match(/session_id=([^;]+)/);
      if (match) {
        sessionId = match[1];
      }
    }
  }

  if (sessionId) {
    await CapacitorCookies.setCookie({
      url: BASE_URL,
      key: 'session_id',
      value: sessionId,
    });
  }

  return true;
}

export async function whoami(): Promise<string | null> {
  const url = `${BASE_URL}/whoami`;

  const response = await CapacitorHttp.get({ url });

  if (response.status < 200 || response.status >= 300) {
    return null;
  }

  return response.data?.user ?? null;
}

export async function logout(): Promise<void> {
  await CapacitorCookies.clearAllCookies();
}
