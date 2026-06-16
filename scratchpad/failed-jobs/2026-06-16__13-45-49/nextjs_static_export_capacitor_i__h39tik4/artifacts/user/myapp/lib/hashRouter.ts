"use client";

/**
 * Pushes a new hash route by setting window.location.hash.
 */
export function navigate(path: string): void {
  if (typeof window !== 'undefined') {
    window.location.hash = path;
  }
}

/**
 * Returns the current route derived from window.location.hash
 * (with a leading / and defaulting to "/" when the hash is empty or "#").
 */
export function currentPath(): string {
  if (typeof window === 'undefined') {
    return '/';
  }

  let hash = window.location.hash;
  if (hash.startsWith('#')) {
    hash = hash.slice(1);
  }

  if (!hash) {
    return '/';
  }

  if (!hash.startsWith('/')) {
    hash = '/' + hash;
  }

  return hash;
}
