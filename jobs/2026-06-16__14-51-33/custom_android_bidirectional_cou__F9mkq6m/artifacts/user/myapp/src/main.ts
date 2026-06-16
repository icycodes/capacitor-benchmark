import Counter from './counter';

async function demo(): Promise<void> {
  // Subscribe to the 'change' event and store the listener handle.
  const handle = await Counter.addListener('change', (data) => {
    console.log('Counter changed:', data.value);
  });

  // Interact with the plugin to trigger events.
  await Counter.increment();     // counter: 0 -> 1, emits "change" with { value: 1 }
  await Counter.increment();     // counter: 1 -> 2, emits "change" with { value: 2 }
  const current = await Counter.getValue(); // reads value, no event emitted
  console.log('Current value:', current.value);
  await Counter.reset();         // counter: 2 -> 0, emits "change" with { value: 0 }

  // Detach the listener cleanly.
  await handle.remove();
}

demo();
