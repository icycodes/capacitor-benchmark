import Counter from './counter';

async function main(): Promise<void> {
  const handle = await Counter.addListener('change', (data: { value: number }) => {
    console.log('Counter changed:', data.value);
  });

  await Counter.increment();
  await Counter.increment();
  await Counter.reset();
  const result = await Counter.getValue();
  console.log('Current value:', result.value);

  await handle.remove();
}

main();