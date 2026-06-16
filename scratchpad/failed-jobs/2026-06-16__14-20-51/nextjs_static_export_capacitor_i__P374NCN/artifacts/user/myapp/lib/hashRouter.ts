"use client";

export function navigate(path: string): void {
  if (typeof window !== "undefined") {
    window.location.hash = path;
  }
}

export function currentPath(): string {
  if (typeof window !== "undefined") {
    const hash = window.location.hash;
    if (hash && hash.length > 1) {
      const path = hash.substring(1);
      return path.startsWith('/') ? path : '/' + path;
    }
  }
  return "/";
}
