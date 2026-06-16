import { PushNotifications } from '@capacitor/push-notifications';

export const initPush = async () => {
  // Register listeners for all four events
  PushNotifications.addListener('registration', (token) => {
    console.log('Push registration success, token: ' + token.value);
  });

  PushNotifications.addListener('registrationError', (error) => {
    console.log('Error on registration: ' + JSON.stringify(error));
  });

  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('Push received: ' + JSON.stringify(notification));
  });

  PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
    console.log('Push action performed: ' + JSON.stringify(notification));
  });

  // Request permission
  const permStatus = await PushNotifications.requestPermissions();

  // Register if granted
  if (permStatus.receive === 'granted') {
    await PushNotifications.register();
  }
};
