import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';

const writeBtn = document.getElementById('write-btn') as HTMLButtonElement | null;
const readBtn = document.getElementById('read-btn') as HTMLButtonElement | null;
const fileContent = document.getElementById('file-content') as HTMLSpanElement | null;

if (writeBtn && readBtn && fileContent) {
  writeBtn.addEventListener('click', async () => {
    await Filesystem.writeFile({
      path: 'demo.txt',
      data: 'Hello Capacitor',
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
  });

  readBtn.addEventListener('click', async () => {
    const result = await Filesystem.readFile({
      path: 'demo.txt',
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
    fileContent.textContent = result.data as string;
  });
}
