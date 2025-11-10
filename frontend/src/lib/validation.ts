/**
 * Validation utilities for user inputs
 */

/**
 * Validate email address format
 * @param email - Email address to validate
 * @returns True if valid, false otherwise
 */
export function validateEmail(email: string): boolean {
  if (!email || typeof email !== 'string') return false;

  // RFC 5322 simplified email regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

/**
 * Get email validation error message
 * @param email - Email address to validate
 * @returns Error message or null if valid
 */
export function getEmailError(email: string): string | null {
  if (!email) return 'Email is required';
  if (!validateEmail(email)) return 'Please enter a valid email address';
  return null;
}

/**
 * Validate password strength
 * Requirements:
 * - At least 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 * - At least one special character
 * @param password - Password to validate
 * @returns True if valid, false otherwise
 */
export function validatePassword(password: string): boolean {
  if (!password || typeof password !== 'string') return false;
  if (password.length < 8) return false;

  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

  return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
}

/**
 * Get password validation error message
 * @param password - Password to validate
 * @returns Error message or null if valid
 */
export function getPasswordError(password: string): string | null {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';

  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

  if (!hasUpperCase) return 'Password must contain at least one uppercase letter';
  if (!hasLowerCase) return 'Password must contain at least one lowercase letter';
  if (!hasNumber) return 'Password must contain at least one number';
  if (!hasSpecialChar) return 'Password must contain at least one special character';

  return null;
}

/**
 * Validate password confirmation matches
 * @param password - Original password
 * @param confirmPassword - Confirmation password
 * @returns True if matching, false otherwise
 */
export function validatePasswordConfirm(password: string, confirmPassword: string): boolean {
  return password === confirmPassword && password.length > 0;
}

/**
 * Get password confirmation error message
 * @param password - Original password
 * @param confirmPassword - Confirmation password
 * @returns Error message or null if valid
 */
export function getPasswordConfirmError(password: string, confirmPassword: string): string | null {
  if (!confirmPassword) return 'Please confirm your password';
  if (!validatePasswordConfirm(password, confirmPassword)) return 'Passwords do not match';
  return null;
}

/**
 * Supported video formats
 */
export const SUPPORTED_VIDEO_FORMATS = [
  'video/mp4',
  'video/quicktime', // .mov
  'video/x-msvideo', // .avi
  'video/x-matroska', // .mkv
  'video/webm',
];

/**
 * Supported video file extensions
 */
export const SUPPORTED_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];

/**
 * Maximum video file size (2GB)
 */
export const MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024; // 2GB in bytes

/**
 * Validate video file format
 * @param file - File to validate
 * @returns True if valid video format, false otherwise
 */
export function validateVideoFormat(file: File): boolean {
  if (!file) return false;

  // Check MIME type
  if (SUPPORTED_VIDEO_FORMATS.includes(file.type)) return true;

  // Fallback: check file extension
  const fileName = file.name.toLowerCase();
  return SUPPORTED_VIDEO_EXTENSIONS.some((ext) => fileName.endsWith(ext));
}

/**
 * Get video format validation error message
 * @param file - File to validate
 * @returns Error message or null if valid
 */
export function getVideoFormatError(file: File | null): string | null {
  if (!file) return 'Please select a video file';

  if (!validateVideoFormat(file)) {
    return `Unsupported video format. Please use: ${SUPPORTED_VIDEO_EXTENSIONS.join(', ')}`;
  }

  if (file.size > MAX_VIDEO_SIZE) {
    return 'Video file size must be less than 2GB';
  }

  return null;
}

/**
 * Validate video file size
 * @param file - File to validate
 * @returns True if valid size, false otherwise
 */
export function validateVideoSize(file: File): boolean {
  return file.size <= MAX_VIDEO_SIZE;
}

/**
 * Validate video title
 * @param title - Title to validate
 * @returns True if valid, false otherwise
 */
export function validateVideoTitle(title: string): boolean {
  if (!title || typeof title !== 'string') return false;
  const trimmed = title.trim();
  return trimmed.length >= 1 && trimmed.length <= 200;
}

/**
 * Get video title validation error message
 * @param title - Title to validate
 * @returns Error message or null if valid
 */
export function getVideoTitleError(title: string): string | null {
  if (!title || title.trim().length === 0) return 'Video title is required';
  if (title.trim().length > 200) return 'Video title must be less than 200 characters';
  return null;
}

/**
 * Validate video description
 * @param description - Description to validate
 * @returns True if valid, false otherwise
 */
export function validateVideoDescription(description: string): boolean {
  if (!description) return true; // Optional field
  return description.length <= 2000;
}

/**
 * Get video description validation error message
 * @param description - Description to validate
 * @returns Error message or null if valid
 */
export function getVideoDescriptionError(description: string): string | null {
  if (description && description.length > 2000) {
    return 'Description must be less than 2000 characters';
  }
  return null;
}

/**
 * Validate keyword for clip search
 * @param keyword - Keyword to validate
 * @returns True if valid, false otherwise
 */
export function validateKeyword(keyword: string): boolean {
  if (!keyword || typeof keyword !== 'string') return false;
  const trimmed = keyword.trim();
  return trimmed.length >= 1 && trimmed.length <= 100;
}

/**
 * Get keyword validation error message
 * @param keyword - Keyword to validate
 * @returns Error message or null if valid
 */
export function getKeywordError(keyword: string): string | null {
  if (!keyword || keyword.trim().length === 0) return 'Keyword is required';
  if (keyword.trim().length > 100) return 'Keyword must be less than 100 characters';
  return null;
}

/**
 * Validate full name
 * @param name - Name to validate
 * @returns True if valid, false otherwise
 */
export function validateFullName(name: string): boolean {
  if (!name || typeof name !== 'string') return false;
  const trimmed = name.trim();
  return trimmed.length >= 1 && trimmed.length <= 100;
}

/**
 * Get full name validation error message
 * @param name - Name to validate
 * @returns Error message or null if valid
 */
export function getFullNameError(name: string): string | null {
  if (!name || name.trim().length === 0) return 'Name is required';
  if (name.trim().length > 100) return 'Name must be less than 100 characters';
  return null;
}

/**
 * Validate URL format
 * @param url - URL to validate
 * @returns True if valid, false otherwise
 */
export function validateUrl(url: string): boolean {
  if (!url || typeof url !== 'string') return false;

  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get URL validation error message
 * @param url - URL to validate
 * @returns Error message or null if valid
 */
export function getUrlError(url: string): string | null {
  if (!url) return 'URL is required';
  if (!validateUrl(url)) return 'Please enter a valid URL';
  return null;
}
