import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';

const writeBtn = document.getElementById('write-btn');
const readBtn = document.getElementById('read-btn');
const fileContent = document.getElementById('file-content');

if (writeBtn && readBtn && fileContent) {
  writeBtn.addEventListener('click', async () => {
    try {
      await Filesystem.writeFile({
        path: 'demo.txt',
        data: 'Hello Capacitor',
        directory: Directory.Data,
        encoding: Encoding.UTF8
      });
    } catch (e) {
      console.error('Error writing file', e);
    }
  });

  readBtn.addEventListener('click', async () => {
    try {
      const result = await Filesystem.readFile({
        path: 'demo.txt',
        directory: Directory.Data,
        encoding: Encoding.UTF8
      });
      fileContent.textContent = result.data as string;
    } catch (e) {
      console.error('Error reading file', e);
    }
  });
}
