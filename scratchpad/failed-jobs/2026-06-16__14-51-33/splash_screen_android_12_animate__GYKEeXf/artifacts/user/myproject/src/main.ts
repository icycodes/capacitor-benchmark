import { SplashScreen } from '@capacitor/splash-screen';

// Entry point for the web app. The Android 12+ splash screen behavior is
// controlled here: the executor must import @capacitor/splash-screen and
// call SplashScreen.hide() only after the browser has painted the first frame.
//
// Hint: nest two requestAnimationFrame() calls so the hide() happens AFTER the
// first paint, not before it.

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

  // Hide the splash screen only after the first frame has been painted.
  // Nesting two requestAnimationFrame calls ensures the hide() happens
  // after the browser has actually drawn the first frame.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      SplashScreen.hide();
    });
  });
}
