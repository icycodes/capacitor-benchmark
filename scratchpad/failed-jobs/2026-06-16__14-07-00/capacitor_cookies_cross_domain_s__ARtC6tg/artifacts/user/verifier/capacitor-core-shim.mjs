// Lightweight, in-process replacement for `@capacitor/core` that:
//   * records every CapacitorCookies call (so the verifier can assert behavior),
//   * keeps a real in-memory cookie jar keyed by request origin,
//   * routes CapacitorHttp through Node's native `http` module so requests go to a
//     real fixture server (no mocking of the candidate's code).
import http from 'node:http';

const cookieJar = new Map();                // key: `${origin}|${name}` -> value
const setCookieLog = [];                    // every CapacitorCookies.setCookie call
const clearAllCookiesLog = [];              // every CapacitorCookies.clearAllCookies call
const httpLog = [];                         // every CapacitorHttp request

export const __log = {
  cookieJar,
  setCookieLog,
  clearAllCookiesLog,
  httpLog,
  reset() {
    cookieJar.clear();
    setCookieLog.length = 0;
    clearAllCookiesLog.length = 0;
    httpLog.length = 0;
  },
};

function originOf(u) {
  try {
    return new URL(u).origin;
  } catch {
    return '';
  }
}

export const CapacitorCookies = {
  async setCookie(opts) {
    const { url, key, value } = opts || {};
    setCookieLog.push({ url, key, value });
    const origin = originOf(url);
    if (origin && key) {
      cookieJar.set(`${origin}|${key}`, String(value ?? ''));
    }
  },
  async getCookies(opts = {}) {
    const origin = originOf(opts.url || '');
    const out = {};
    for (const [k, v] of cookieJar.entries()) {
      const [coOrigin, coKey] = k.split('|');
      if (!origin || coOrigin === origin) out[coKey] = v;
    }
    return out;
  },
  async deleteCookie({ url, key }) {
    const origin = originOf(url);
    cookieJar.delete(`${origin}|${key}`);
  },
  async clearCookies({ url }) {
    const origin = originOf(url);
    for (const k of [...cookieJar.keys()]) {
      if (k.startsWith(`${origin}|`)) cookieJar.delete(k);
    }
  },
  async clearAllCookies() {
    clearAllCookiesLog.push({ at: Date.now() });
    cookieJar.clear();
  },
};

function cookieHeaderFor(origin) {
  const parts = [];
  for (const [k, v] of cookieJar.entries()) {
    const [coOrigin, coKey] = k.split('|');
    if (coOrigin === origin) parts.push(`${coKey}=${v}`);
  }
  return parts.length ? parts.join('; ') : '';
}

function applySetCookieHeader(origin, setCookieHeader) {
  if (!setCookieHeader) return;
  const items = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader];
  for (const raw of items) {
    if (typeof raw !== 'string') continue;
    const first = raw.split(';')[0];
    const eq = first.indexOf('=');
    if (eq <= 0) continue;
    const name = first.slice(0, eq).trim();
    const value = first.slice(eq + 1).trim();
    cookieJar.set(`${origin}|${name}`, value);
  }
}

function nativeRequest(urlString, method, headers, dataBody) {
  return new Promise((resolve, reject) => {
    let parsed;
    try {
      parsed = new URL(urlString);
    } catch (e) {
      reject(e);
      return;
    }
    const origin = parsed.origin;
    const reqHeaders = { ...(headers || {}) };
    const cookieHeader = cookieHeaderFor(origin);
    if (cookieHeader && !reqHeaders.Cookie && !reqHeaders.cookie) {
      reqHeaders.Cookie = cookieHeader;
    }

    let payload;
    if (dataBody !== undefined && dataBody !== null && method !== 'GET' && method !== 'HEAD') {
      if (typeof dataBody === 'string') {
        payload = dataBody;
      } else {
        payload = JSON.stringify(dataBody);
        if (!reqHeaders['Content-Type'] && !reqHeaders['content-type']) {
          reqHeaders['Content-Type'] = 'application/json';
        }
      }
    }

    const req = http.request({
      method,
      hostname: parsed.hostname,
      port: parsed.port || 80,
      path: parsed.pathname + parsed.search,
      headers: reqHeaders,
    }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks).toString('utf-8');
        applySetCookieHeader(origin, res.headers['set-cookie']);
        const ct = (res.headers['content-type'] || '').toLowerCase();
        let parsedBody = buf;
        if (ct.includes('json')) {
          try { parsedBody = JSON.parse(buf); } catch { /* fall back to raw */ }
        }
        const response = {
          status: res.statusCode || 0,
          data: parsedBody,
          headers: res.headers,
          url: urlString,
        };
        httpLog.push({ url: urlString, method, status: response.status });
        resolve(response);
      });
    });
    req.on('error', reject);
    if (payload !== undefined) req.write(payload);
    req.end();
  });
}

async function doRequest(opts) {
  const method = (opts.method || 'GET').toUpperCase();
  return nativeRequest(opts.url, method, opts.headers, opts.data);
}

export const CapacitorHttp = {
  request: (opts) => doRequest(opts),
  get: (opts) => doRequest({ ...opts, method: 'GET' }),
  post: (opts) => doRequest({ ...opts, method: 'POST' }),
  put: (opts) => doRequest({ ...opts, method: 'PUT' }),
  patch: (opts) => doRequest({ ...opts, method: 'PATCH' }),
  delete: (opts) => doRequest({ ...opts, method: 'DELETE' }),
};

export const registerPlugin = () => {
  throw new Error('registerPlugin is not used by this task; not implemented in shim.');
};

export default { CapacitorCookies, CapacitorHttp, registerPlugin };
