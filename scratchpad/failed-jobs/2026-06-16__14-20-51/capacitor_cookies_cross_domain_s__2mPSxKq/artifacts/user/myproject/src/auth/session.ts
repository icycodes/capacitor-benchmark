import { CapacitorCookies, CapacitorHttp } from '@capacitor/core';

const getBaseUrl = (): string => {
  return process.env.API_BASE_URL || '';
};

export async function login(user: string, pass: string): Promise<boolean> {
  const baseUrl = getBaseUrl();
  try {
    const response = await CapacitorHttp.post({
      url: `${baseUrl}/login`,
      headers: {
        'Content-Type': 'application/json',
      },
      data: { user, pass },
    });

    if (response.status >= 200 && response.status < 300) {
      let sessionId = response.data?.session_id;
      
      if (!sessionId && response.headers) {
        const setCookie: unknown = response.headers['Set-Cookie'] || response.headers['set-cookie'];
        if (typeof setCookie === 'string') {
          const match = setCookie.match(/session_id=([^;]+)/);
          if (match) {
            sessionId = match[1];
          }
        } else if (Array.isArray(setCookie)) {
          for (const cookie of setCookie) {
            if (typeof cookie === 'string') {
              const match = cookie.match(/session_id=([^;]+)/);
              if (match) {
                sessionId = match[1];
                break;
              }
            }
          }
        }
      }

      if (sessionId) {
        await CapacitorCookies.setCookie({
          url: baseUrl,
          key: 'session_id',
          value: sessionId,
        });
      }
      return true;
    }
  } catch (error) {
    // Ignore error
  }
  return false;
}

export async function whoami(): Promise<string | null> {
  const baseUrl = getBaseUrl();
  try {
    const response = await CapacitorHttp.get({
      url: `${baseUrl}/whoami`,
    });

    if (response.status >= 200 && response.status < 300) {
      return response.data?.user || null;
    }
  } catch (error) {
    // Ignore error
  }
  return null;
}

export async function logout(): Promise<void> {
  await CapacitorCookies.clearAllCookies();
}
