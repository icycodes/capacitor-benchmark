import { PushNotifications } from '@capacitor/push-notifications';

export async function initPush() {
  // 1. Register listeners for all four events
  await PushNotifications.addListener('registration', (token) => {
    console.log('Push registration success, token: ' + token.value);
  });

  await PushNotifications.addListener('registrationError', (error) => {
    console.error('Push registration error: ' + error.error);
  });

  await PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('Push notification received: ', notification);
  });

  await PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
    console.log('Push notification action performed: ', notification);
  });

  // 2. Call requestPermissions() and, only when the returned receive value is 'granted', call register()
  const permStatus = await PushNotifications.requestPermissions();
  if (permStatus.receive === 'granted') {
    await PushNotifications.register();
  }
}
