import { PushNotifications } from '@capacitor/push-notifications';

/**
 * Initialise Firebase Cloud Messaging push notifications.
 *
 * Order of operations (per Capacitor plugin docs):
 *   1. Register all event listeners.
 *   2. Request runtime permission.
 *   3. Call register() only when permission is granted.
 */
export async function initPush(): Promise<void> {
  // ── 1. Register listeners BEFORE requesting permission ──────────────────

  PushNotifications.addListener('registration', (token) => {
    console.log('[Push] Registration token:', token.value);
  });

  PushNotifications.addListener('registrationError', (error) => {
    console.error('[Push] Registration error:', error.error);
  });

  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('[Push] Notification received:', notification);
  });

  PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
    console.log('[Push] Notification action performed:', action.actionId, action.notification);
  });

  // ── 2. Request permission ────────────────────────────────────────────────

  const permissionStatus = await PushNotifications.requestPermissions();

  // ── 3. Register only when the user granted permission ───────────────────

  if (permissionStatus.receive === 'granted') {
    await PushNotifications.register();
  } else {
    console.warn('[Push] Permission not granted; status:', permissionStatus.receive);
  }
}
