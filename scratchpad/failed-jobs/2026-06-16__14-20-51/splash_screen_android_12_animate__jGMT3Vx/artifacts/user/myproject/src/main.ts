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

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      SplashScreen.hide();
    });
  });
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
}
