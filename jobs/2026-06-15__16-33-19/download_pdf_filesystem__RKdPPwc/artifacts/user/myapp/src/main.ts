import { Filesystem, Directory } from '@capacitor/filesystem';

const FILE_PATH = 'sample.pdf';

/** Convert an ArrayBuffer to a base64 string (no data-URL prefix). */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/** Decode a base64 string back to an ArrayBuffer. */
function base64ToArrayBuffer(b64: string): ArrayBuffer {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/** Compute a lowercase hex SHA-256 digest of the given ArrayBuffer. */
async function sha256Hex(buffer: ArrayBuffer): Promise<string> {
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

function setStatus(text: string): void {
  const el = document.getElementById('download-status');
  if (el) el.textContent = text;
}

function setFileSize(value: string): void {
  const el = document.getElementById('file-size');
  if (el) el.textContent = value;
}

function setFileSha256(value: string): void {
  const el = document.getElementById('file-sha256');
  if (el) el.textContent = value;
}

async function downloadAndSave(): Promise<void> {
  setStatus('downloading');
  setFileSize('');
  setFileSha256('');

  try {
    // 1. Fetch the PDF from the same origin.
    const response = await fetch('/sample.pdf');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }
    const arrayBuffer = await response.arrayBuffer();

    // 2. Encode to base64 for Capacitor Filesystem.
    const base64Data = arrayBufferToBase64(arrayBuffer);

    // 3. Write through Capacitor Filesystem (persisted in IndexedDB on web).
    await Filesystem.writeFile({
      path: FILE_PATH,
      data: base64Data,
      directory: Directory.Documents,
    });

    // 4. Read the file back from Capacitor Filesystem to prove persistence.
    const readResult = await Filesystem.readFile({
      path: FILE_PATH,
      directory: Directory.Documents,
    });

    // The data returned is a base64 string on web/native.
    const persistedBase64 = readResult.data as string;
    const persistedBuffer = base64ToArrayBuffer(persistedBase64);

    // 5. Compute size and SHA-256 from the persisted bytes.
    const byteSize = persistedBuffer.byteLength;
    const digest = await sha256Hex(persistedBuffer);

    setFileSize(String(byteSize));
    setFileSha256(digest);
    setStatus('saved');
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    setStatus(`error: ${message}`);
  }
}

// Wire up the button once the DOM is ready.
const btn = document.getElementById('download-pdf');
if (btn) {
  btn.addEventListener('click', () => {
    downloadAndSave().catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      setStatus(`error: ${message}`);
    });
  });
}
