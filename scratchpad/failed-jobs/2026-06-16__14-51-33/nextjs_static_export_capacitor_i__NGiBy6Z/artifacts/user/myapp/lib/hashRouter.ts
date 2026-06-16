"use client";

/**
 * Push a new hash route by setting window.location.hash.
 */
export function navigate(path: string): void {
  if (typeof window === "undefined") return;
  window.location.hash = path;
}

/**
 * Return the current route derived from window.location.hash.
 * Defaults to "/" when the hash is empty or "#".
 */
export function currentPath(): string {
  if (typeof window === "undefined") return "/";
  const hash = window.location.hash;
  if (!hash || hash === "#") return "/";
  // Strip the leading '#' and ensure it starts with '/'
  const path = hash.startsWith("#/") ? hash.slice(1) : "/" + hash.slice(1);
  return path || "/";
}
