import { App, URLOpenListenerEvent } from '@capacitor/app';

export function registerDeeplinkHandler(): void {
  App.addListener('appUrlOpen', (event: URLOpenListenerEvent) => {
    if (event && event.url) {
      try {
        const parsedUrl = new URL(event.url);
        window.location.replace(parsedUrl.pathname);
      } catch (e) {
        console.error('Failed to parse deep-link URL:', e);
      }
    }
  });
}
