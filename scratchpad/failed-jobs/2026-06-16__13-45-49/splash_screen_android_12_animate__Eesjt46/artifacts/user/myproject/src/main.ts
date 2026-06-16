import { SplashScreen } from '@capacitor/splash-screen';

function bootstrap(): void {
  const root = document.getElementById('root');
  if (root) {
    root.textContent = 'Welcome to My Native App';
  }

  // Hide the splash screen after the first frame has been painted
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
