import Counter from './counter';

async function main(): Promise<void> {
  // Subscribe to the native 'change' event; store the listener handle.
  const listenerHandle = await Counter.addListener('change', (event) => {
    console.log('[Counter] change event received, value =', event.value);
  });

  // Drive native state: increment three times, then reset.
  const r1 = await Counter.increment();
  console.log('[Counter] after increment:', r1.value); // 1

  const r2 = await Counter.increment();
  console.log('[Counter] after increment:', r2.value); // 2

  const r3 = await Counter.increment();
  console.log('[Counter] after increment:', r3.value); // 3

  const r4 = await Counter.reset();
  console.log('[Counter] after reset:', r4.value); // 0

  const r5 = await Counter.getValue();
  console.log('[Counter] getValue:', r5.value); // 0 (no change event emitted)

  // Deterministically detach the listener via the handle.
  await listenerHandle.remove();
  console.log('[Counter] listener removed');
}

main().catch((err) => console.error('[Counter] error:', err));
