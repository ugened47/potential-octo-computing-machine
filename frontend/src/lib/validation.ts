/** Form validation utilities. */

/**
 * Validate email format.
 * @param email - Email address to validate
 * @returns True if valid, false otherwise
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate password strength.
 * @param password - Password to validate
 * @returns Object with validation result and error message
 */
export function validatePassword(password: string): {
  valid: boolean
  error?: string
} {
  if (password.length < 8) {
    return { valid: false, error: 'Password must be at least 8 characters long' }
  }

  if (!/[A-Z]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one uppercase letter' }
  }

  if (!/[a-z]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one lowercase letter' }
  }

  if (!/[0-9]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one number' }
  }

  return { valid: true }
}

/**
 * Validate required field.
 * @param value - Value to validate
 * @param fieldName - Name of field for error message
 * @returns Object with validation result and error message
 */
export function validateRequired(
  value: string | undefined | null,
  fieldName: string
): {
  valid: boolean
  error?: string
} {
  if (!value || value.trim() === '') {
    return { valid: false, error: `${fieldName} is required` }
  }
  return { valid: true }
}

/**
 * Validate file size.
 * @param file - File to validate
 * @param maxSizeBytes - Maximum size in bytes
 * @returns Object with validation result and error message
 */
export function validateFileSize(
  file: File,
  maxSizeBytes: number
): {
  valid: boolean
  error?: string
} {
  if (file.size > maxSizeBytes) {
    const maxSizeMB = Math.round(maxSizeBytes / (1024 * 1024))
    return { valid: false, error: `File size must be less than ${maxSizeMB}MB` }
  }
  return { valid: true }
}

/**
 * Validate file type.
 * @param file - File to validate
 * @param allowedTypes - Array of allowed MIME types
 * @returns Object with validation result and error message
 */
export function validateFileType(
  file: File,
  allowedTypes: string[]
): {
  valid: boolean
  error?: string
} {
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: `File type ${file.type} is not allowed` }
  }
  return { valid: true }
}

/**
 * Validate URL format.
 * @param url - URL to validate
 * @returns True if valid, false otherwise
 */
export function validateUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Validate phone number format (basic).
 * @param phone - Phone number to validate
 * @returns True if valid, false otherwise
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^\+?[\d\s\-()]+$/
  return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10
}
