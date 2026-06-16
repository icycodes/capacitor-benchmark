import { App } from '@capacitor/app';

export function registerDeepLinks() {
  App.addListener('appUrlOpen', (event) => {
    const url = new URL(event.url);
    const pathname = url.pathname;
    window.location.replace(pathname);
  });
}
