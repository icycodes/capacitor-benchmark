import Counter from './counter';

async function runDemo() {
  console.log('Starting Counter plugin demo...');

  // Subscribe to 'change' event
  const listenerHandle = await Counter.addListener('change', (state) => {
    console.log(`[Event] Counter changed: ${state.value}`);
  });

  try {
    // Get initial value
    const initial = await Counter.getValue();
    console.log(`Initial value: ${initial.value}`);

    // Increment
    const inc1 = await Counter.increment();
    console.log(`After increment: ${inc1.value}`);

    // Increment again
    const inc2 = await Counter.increment();
    console.log(`After second increment: ${inc2.value}`);

    // Reset
    const res = await Counter.reset();
    console.log(`After reset: ${res.value}`);
  } catch (error) {
    console.error('Error during demo:', error);
  } finally {
    // Deterministically detach the listener
    await listenerHandle.remove();
    console.log('Listener handle removed. Demo finished.');
  }
}

runDemo();
