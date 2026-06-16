import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';

const writeBtn = document.getElementById('write-btn');
const readBtn = document.getElementById('read-btn');
const fileContent = document.getElementById('file-content');

if (writeBtn) {
  writeBtn.addEventListener('click', async () => {
    try {
      await Filesystem.writeFile({
        path: 'demo.txt',
        data: 'Hello Capacitor',
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });
      console.log('File written successfully');
    } catch (err) {
      console.error('Error writing file', err);
    }
  });
}

if (readBtn) {
  readBtn.addEventListener('click', async () => {
    try {
      const result = await Filesystem.readFile({
        path: 'demo.txt',
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });
      if (fileContent) {
        if (typeof result.data === 'string') {
          fileContent.textContent = result.data;
        } else {
          fileContent.textContent = String(result.data);
        }
      }
    } catch (err) {
      console.error('Error reading file', err);
      if (fileContent) {
        fileContent.textContent = '';
      }
    }
  });
}
