/**
 * Lightweight client-side hash-based routing helper.
 *
 * Safe to import from client components only — reads `window.location.hash`.
 * On the server (SSR / static generation) `window` is undefined, so both
 * functions guard against that and return safe defaults.
 */

/**
 * Navigate to the given path by setting it as the current URL hash.
 * e.g. navigate('/about') → window.location.hash = '/about'
 */
export function navigate(path: string): void {
  if (typeof window !== 'undefined') {
    window.location.hash = path;
  }
}

/**
 * Return the current route derived from `window.location.hash`.
 * The leading `#` character is stripped and a leading `/` is always ensured.
 * Defaults to `"/"` when the hash is empty or equals `"#"`.
 *
 * Examples:
 *   hash = ""        → "/"
 *   hash = "#"       → "/"
 *   hash = "#/about" → "/about"
 *   hash = "#about"  → "/about"
 */
export function currentPath(): string {
  if (typeof window === 'undefined') {
    return '/';
  }

  const hash = window.location.hash;

  // Strip the leading '#'
  const withoutHash = hash.startsWith('#') ? hash.slice(1) : hash;

  if (!withoutHash || withoutHash === '/') {
    return '/';
  }

  // Ensure a leading slash
  return withoutHash.startsWith('/') ? withoutHash : `/${withoutHash}`;
}
