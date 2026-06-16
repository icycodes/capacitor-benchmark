import Counter from './counter';

async function run() {
  const handle = await Counter.addListener('change', (state) => {
    console.log('Counter changed to:', state.value);
  });

  await Counter.increment();
  await Counter.increment();
  await Counter.reset();
  const val = await Counter.getValue();
  console.log('Final value:', val.value);

  await handle.remove();
}

run();
