import { PushNotifications } from '@capacitor/push-notifications';

export function initPush(): void {
  // 1. Register listeners for all four events
  PushNotifications.addListener('registration', (token) => {
    console.log('Push registration token:', token.value);
  });

  PushNotifications.addListener('registrationError', (error) => {
    console.error('Push registration error:', error);
  });

  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('Push notification received:', notification);
  });

  PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
    console.log('Push notification action performed:', notification);
  });

  // 2. Request permissions, and only register when receive is 'granted'
  PushNotifications.requestPermissions().then((result) => {
    if (result.receive === 'granted') {
      PushNotifications.register();
    }
  });
}
