"use client";

/**
 * Navigate to a new hash-based route.
 * Sets window.location.hash to the given path.
 */
export function navigate(path: string): void {
  if (typeof window !== "undefined") {
    window.location.hash = path;
  }
}

/**
 * Returns the current route derived from window.location.hash.
 * Defaults to "/" when the hash is empty or just "#".
 * Always returns a string starting with "/".
 */
export function currentPath(): string {
  if (typeof window !== "undefined") {
    const hash = window.location.hash;
    if (!hash || hash === "#") {
      return "/";
    }
    // Remove the leading "#" and ensure the path starts with "/"
    const path = hash.replace(/^#/, "");
    return path.startsWith("/") ? path : "/" + path;
  }
  return "/";
}