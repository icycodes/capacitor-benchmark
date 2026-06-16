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

  PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
    console.log('Push notification action performed:', action);
  });

  // 2. Request permissions and register only when granted
  PushNotifications.requestPermissions().then((result) => {
    if (result.receive === 'granted') {
      // 3. Register for push notifications
      PushNotifications.register();
    }
  });
}