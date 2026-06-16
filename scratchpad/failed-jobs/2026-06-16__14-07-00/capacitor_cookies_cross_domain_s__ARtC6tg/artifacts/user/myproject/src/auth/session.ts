import { CapacitorCookies, CapacitorHttp } from '@capacitor/core';

const API_BASE_URL: string = process.env['API_BASE_URL'] ?? '';

/**
 * Log in with the given credentials.
 * POSTs to <API_BASE_URL>/login with JSON body { user, pass }.
 * On a 2xx response, stores the returned session_id cookie in the native
 * WebView cookie store and returns true.  Returns false otherwise.
 */
export async function login(user: string, pass: string): Promise<boolean> {
  const response = await CapacitorHttp.post({
    url: `${API_BASE_URL}/login`,
    headers: { 'Content-Type': 'application/json' },
    data: { user, pass },
  });

  if (response.status < 200 || response.status > 299) {
    return false;
  }

  // Extract session_id from the parsed JSON body first, then fall back to a
  // Set-Cookie response header.
  let sessionId: string | undefined;

  if (
    response.data !== null &&
    typeof response.data === 'object' &&
    typeof (response.data as Record<string, unknown>)['session_id'] === 'string'
  ) {
    sessionId = (response.data as Record<string, string>)['session_id'];
  } else if (typeof response.headers['set-cookie'] === 'string') {
    // Best-effort parse of the first "session_id=<value>" segment.
    const match = /(?:^|;)\s*session_id=([^;]+)/.exec(
      response.headers['set-cookie'],
    );
    if (match) {
      sessionId = match[1];
    }
  }

  if (sessionId !== undefined) {
    await CapacitorCookies.setCookie({
      url: API_BASE_URL,
      key: 'session_id',
      value: sessionId,
    });
  }

  return true;
}

/**
 * Returns the currently authenticated username by calling <API_BASE_URL>/whoami.
 * CapacitorHttp automatically sends cookies from the native store, so no
 * manual cookie header is required.
 * Returns the `user` field from the JSON response on success, or null on failure.
 */
export async function whoami(): Promise<string | null> {
  const response = await CapacitorHttp.get({
    url: `${API_BASE_URL}/whoami`,
  });

  if (response.status < 200 || response.status > 299) {
    return null;
  }

  if (
    response.data !== null &&
    typeof response.data === 'object' &&
    typeof (response.data as Record<string, unknown>)['user'] === 'string'
  ) {
    return (response.data as Record<string, string>)['user'];
  }

  return null;
}

/**
 * Clears all cookies from the native WebView cookie store, effectively
 * terminating the current session.
 */
export async function logout(): Promise<void> {
  await CapacitorCookies.clearAllCookies();
}
