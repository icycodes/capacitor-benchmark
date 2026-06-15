import { Filesystem, Directory, Encoding } from "@capacitor/filesystem";

const statusEl = document.getElementById("download-status")!;
const sizeEl = document.getElementById("file-size")!;
const shaEl = document.getElementById("file-sha256")!;
const buttonEl = document.getElementById("download-pdf")!;

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

async function sha256(buffer: ArrayBuffer): Promise<string> {
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

buttonEl.addEventListener("click", async () => {
  // Reset display
  sizeEl.textContent = "";
  shaEl.textContent = "";
  statusEl.textContent = "downloading";

  try {
    // 1. Download the PDF
    const response = await fetch("/sample.pdf");
    if (!response.ok) {
      statusEl.textContent = `error: HTTP ${response.status} ${response.statusText}`;
      return;
    }
    const pdfBuffer = await response.arrayBuffer();

    // 2. Convert to base64 and write via Capacitor Filesystem
    const base64Data = arrayBufferToBase64(pdfBuffer);
    await Filesystem.writeFile({
      path: "sample.pdf",
      data: base64Data,
      directory: Directory.Documents,
    });

    // 3. Read the file back from Capacitor Filesystem to prove persistence
    const result = await Filesystem.readFile({
      path: "sample.pdf",
      directory: Directory.Documents,
    });

    // result.data is a base64 string (no encoding specified)
    const readBackBuffer = base64ToArrayBuffer(result.data as string);

    // 4. Compute size and SHA-256 from the read-back data
    const fileSize = readBackBuffer.byteLength;
    const hexDigest = await sha256(readBackBuffer);

    // 5. Update the UI
    sizeEl.textContent = String(fileSize);
    shaEl.textContent = hexDigest;
    statusEl.textContent = "saved";
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    statusEl.textContent = `error: ${message}`;
  }
});
