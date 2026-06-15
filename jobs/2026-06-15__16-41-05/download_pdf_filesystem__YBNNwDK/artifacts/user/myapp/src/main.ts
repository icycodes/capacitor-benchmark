import { Filesystem, Directory } from '@capacitor/filesystem';

const downloadBtn = document.getElementById('download-pdf') as HTMLButtonElement;
const statusDiv = document.getElementById('download-status') as HTMLDivElement;
const sizeDiv = document.getElementById('file-size') as HTMLDivElement;
const sha256Div = document.getElementById('file-sha256') as HTMLDivElement;

function arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary_string = window.atob(base64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

async function computeSHA256(buffer: ArrayBuffer): Promise<string> {
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

downloadBtn.addEventListener('click', async () => {
    try {
        statusDiv.textContent = 'downloading';
        sizeDiv.textContent = '';
        sha256Div.textContent = '';

        const response = await fetch('/sample.pdf');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const buffer = await response.arrayBuffer();
        const base64Data = arrayBufferToBase64(buffer);

        await Filesystem.writeFile({
            path: 'sample.pdf',
            data: base64Data,
            directory: Directory.Documents
        });

        const readResult = await Filesystem.readFile({
            path: 'sample.pdf',
            directory: Directory.Documents
        });

        let readBuffer: ArrayBuffer;
        if (typeof readResult.data === 'string') {
            readBuffer = base64ToArrayBuffer(readResult.data);
        } else if (readResult.data instanceof Blob) {
            readBuffer = await readResult.data.arrayBuffer();
        } else {
            throw new Error('Unexpected data type from readFile');
        }

        const size = readBuffer.byteLength;
        const sha256 = await computeSHA256(readBuffer);

        sizeDiv.textContent = size.toString();
        sha256Div.textContent = sha256;
        statusDiv.textContent = 'saved';

    } catch (e: any) {
        statusDiv.textContent = `error: ${e.message}`;
    }
});
