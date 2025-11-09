/** Validation utilities. */

const ALLOWED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".webm", ".mkv"];
const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024; // 2GB

/**
 * Validate video file format.
 */
export function validateVideoFormat(filename: string): boolean {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf("."));
  return ALLOWED_VIDEO_FORMATS.includes(ext);
}

/**
 * Validate video file size.
 */
export function validateVideoSize(
  sizeInBytes: number,
  maxSizeMB?: number,
): boolean {
  const maxSize = maxSizeMB ? maxSizeMB * 1024 * 1024 : MAX_FILE_SIZE_BYTES;
  return sizeInBytes <= maxSize;
}

/**
 * Get video MIME type from filename.
 */
export function getVideoMimeType(filename: string): string {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf("."));
  const mimeTypes: Record<string, string> = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
  };
  return mimeTypes[ext] || "video/mp4";
}
