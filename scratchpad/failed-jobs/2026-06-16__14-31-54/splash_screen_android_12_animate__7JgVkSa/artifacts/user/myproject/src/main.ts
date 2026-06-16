import { SplashScreen } from '@capacitor/splash-screen';

// Entry point for the web app. The Android 12+ splash screen behavior is
// controlled here: we hide the splash only after the browser has painted
// the first frame, using nested requestAnimationFrame() calls.

function bootstrap(): void {
  const root = document.getElementById('root');
  if (root) {
    root.textContent = 'Welcome to My Native App';
  }

  // Hide the splash screen after the first frame has been painted.
  // The outer requestAnimationFrame schedules work for the next paint;
  // the inner one ensures we are called AFTER that paint completes.
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