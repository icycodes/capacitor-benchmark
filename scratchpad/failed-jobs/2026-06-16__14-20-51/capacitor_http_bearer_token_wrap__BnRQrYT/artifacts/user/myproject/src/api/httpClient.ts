import { CapacitorHttp, HttpOptions, HttpResponse } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  status: 401;
  url: string;

  constructor(url: string) {
    super(`Unauthorized: ${url}`);
    this.name = 'UnauthorizedError';
    this.status = 401;
    this.url = url;
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}

async function doRequest<T>(options: HttpOptions): Promise<ApiResponse<T>> {
  const { value: token } = await Preferences.get({ key: 'auth_token' });
  const headers: Record<string, string> = options.headers ? { ...options.headers } : {};

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  options.headers = headers;

  const response: HttpResponse = await CapacitorHttp.request(options);

  if (response.status === 401) {
    await Preferences.remove({ key: 'auth_token' });
    throw new UnauthorizedError(options.url);
  }

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`HTTP ${response.status}`);
  }

  return {
    data: response.data as T,
    status: response.status,
    headers: response.headers,
  };
}

export function httpGet<T = unknown>(
  url: string,
  params?: Record<string, string>,
): Promise<ApiResponse<T>> {
  const options: HttpOptions = {
    method: 'GET',
    url,
  };

  if (params) {
    options.params = params;
  }

  return doRequest<T>(options);
}

export function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>> {
  const options: HttpOptions = {
    method: 'POST',
    url,
    headers: {},
  };

  if (body !== undefined) {
    options.data = body;
    if (options.headers) {
      options.headers['Content-Type'] = 'application/json';
    }
  }

  return doRequest<T>(options);
}
