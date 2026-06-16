// Entry point for the web app. The Android 12+ splash screen behavior is
// controlled here: the executor must import @capacitor/splash-screen and
// call SplashScreen.hide() only after the browser has painted the first frame.
//
// Hint: nest two requestAnimationFrame() calls so the hide() happens AFTER the
// first paint, not before it.

import { SplashScreen } from '@capacitor/splash-screen';

function bootstrap(): void {
  const root = document.getElementById('root');
  if (root) {
    root.textContent = 'Welcome to My Native App';
  }
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
}

// Hide the splash screen only after the first frame has been painted.
// The outer rAF queues work before paint; the inner rAF fires after the
// browser has actually committed the first frame to screen.
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    SplashScreen.hide();
  });
});
