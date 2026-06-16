import { App } from '@capacitor/app';

export function setupDeepLinkHandler(): void {
  App.addListener('appUrlOpen', (event) => {
    const pathname = new URL(event.url).pathname;
    window.location.replace(pathname);
  });
}