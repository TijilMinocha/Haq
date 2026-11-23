import imageCompression from 'browser-image-compression';

const MAX_DIMENSION_PX = 1600;
const QUALITY = 0.7;

/** Shrinks photos for weak networks. PDFs pass through untouched. */
export async function compressImage(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) return file;
  const compressed = await imageCompression(file, {
    maxWidthOrHeight: MAX_DIMENSION_PX,
    initialQuality: QUALITY,
    fileType: 'image/jpeg',
    useWebWorker: true,
  });
  const name = file.name.replace(/\.[^.]+$/, '') + '.jpg';
  return new File([compressed], name, { type: 'image/jpeg' });
}
