// End-to-end behavioral verifier for src/auth/session.ts.
// Flow:
//   1. Register an ESM resolver hook that redirects `@capacitor/core` to our shim.
//   2. Start a real local fixture HTTP server.
//   3. Set process.env.API_BASE_URL so the candidate module reads our origin.
//   4. Dynamically import the compiled session module and run the four assertions.
import { register } from 'node:module';
register('./capacitor-loader.mjs', import.meta.url);

const SHIM_URL = new URL('./capacitor-core-shim.mjs', import.meta.url).href;
const shim = await import(SHIM_URL);
const { __log } = shim;

const { startFixtureServer } = await import('./server.mjs');

const failures = [];
function fail(msg) { failures.push(msg); }

const COMPILED_SESSION = process.env.COMPILED_SESSION_PATH || '/tmp/verify-build/auth/session.js';
const { server, port } = await startFixtureServer();
process.env.API_BASE_URL = `http://127.0.0.1:${port}`;

try {
  let sessionMod;
  try {
    sessionMod = await import(`file://${COMPILED_SESSION}?t=${Date.now()}`);
  } catch (e) {
    fail(`Could not import compiled session module at ${COMPILED_SESSION}: ${e && e.stack ? e.stack : e}`);
    sessionMod = {};
  }
  const { login, whoami, logout } = sessionMod;

  if (typeof login !== 'function') fail(`Expected 'login' to be an exported function; got ${typeof login}.`);
  if (typeof whoami !== 'function') fail(`Expected 'whoami' to be an exported function; got ${typeof whoami}.`);
  if (typeof logout !== 'function') fail(`Expected 'logout' to be an exported function; got ${typeof logout}.`);

  if (typeof login === 'function' && typeof whoami === 'function' && typeof logout === 'function') {
    // --- Case A: positive login ---
    __log.reset();
    let loginOk;
    try { loginOk = await login('alice', 'wonderland'); }
    catch (e) { fail(`Case A: login('alice','wonderland') threw: ${e && e.stack ? e.stack : e}`); }
    if (loginOk !== true) fail(`Case A: expected login to return boolean true; got ${JSON.stringify(loginOk)}.`);
    const okCookie = __log.setCookieLog.find((e) => e && e.key === 'session_id' && e.value === 'SESSION_TOKEN');
    if (!okCookie) fail(`Case A: expected CapacitorCookies.setCookie call with key='session_id', value='SESSION_TOKEN'. setCookieLog=${JSON.stringify(__log.setCookieLog)}`);

    // --- Case B: whoami after login ---
    let who;
    try { who = await whoami(); }
    catch (e) { fail(`Case B: whoami() threw: ${e && e.stack ? e.stack : e}`); }
    if (who !== 'alice') fail(`Case B: expected whoami() to return 'alice'; got ${JSON.stringify(who)}.`);

    // --- Case C: negative login (no prior session in jar) ---
    __log.reset();
    let loginBad;
    try { loginBad = await login('alice', 'bad'); }
    catch (e) { fail(`Case C: login('alice','bad') threw: ${e && e.stack ? e.stack : e}`); }
    if (loginBad !== false) fail(`Case C: expected login('alice','bad') to return boolean false; got ${JSON.stringify(loginBad)}.`);

    // --- Case D: logout calls clearAllCookies ---
    __log.reset();
    try { await logout(); }
    catch (e) { fail(`Case D: logout() threw: ${e && e.stack ? e.stack : e}`); }
    if (__log.clearAllCookiesLog.length < 1) fail(`Case D: expected logout() to invoke CapacitorCookies.clearAllCookies at least once. clearAllCookiesLog is empty.`);
  }
} catch (e) {
  fail(`Verifier threw: ${e && e.stack ? e.stack : e}`);
} finally {
  try { server.close(); } catch {}
}

if (failures.length === 0) {
  console.log('RESULT: PASS');
  process.exit(0);
} else {
  for (const f of failures) console.error('FAILURE:', f);
  console.log('RESULT: FAIL');
  process.exit(1);
}
