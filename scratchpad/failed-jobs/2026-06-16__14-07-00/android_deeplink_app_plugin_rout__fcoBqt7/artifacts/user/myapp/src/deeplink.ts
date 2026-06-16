import { App } from '@capacitor/app';

/**
 * Registers a listener for Android App Links / Universal Links.
 *
 * When the app is launched or resumed via an https://myapp.example.com/...
 * URL, the `appUrlOpen` event fires with the full URL.  We parse out the
 * pathname and hand it to the SPA router so the correct view is rendered
 * without a full page reload.
 *
 * Call this function once from your app entry point (e.g. src/index.ts).
 */
export function registerDeepLinkHandler(): void {
  App.addListener('appUrlOpen', (event) => {
    const url = new URL(event.url);
    const pathname = url.pathname;

    // Drive the SPA to the matching route.
    // Replace the current history entry so the user can still press Back to
    // leave the app rather than looping back through the deep-link URL.
    window.history.replaceState(null, '', pathname);

    // Dispatch a popstate event so any in-app router (e.g. a history-based
    // router) picks up the location change and renders the right component.
    window.dispatchEvent(new PopStateEvent('popstate', { state: null }));
  });
}
