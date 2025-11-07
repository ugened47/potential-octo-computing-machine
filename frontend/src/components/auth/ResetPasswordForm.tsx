'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { resetPassword } from '@/lib/auth-api'
import { validatePassword } from '@/lib/validation'
import { Loader2, AlertCircle } from 'lucide-react'

export function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [confirmPasswordError, setConfirmPasswordError] = useState('')
  const [generalError, setGeneralError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTokenValid, setIsTokenValid] = useState(true)

  useEffect(() => {
    if (!token) {
      setIsTokenValid(false)
      setGeneralError('Invalid or missing reset token')
    }
  }, [token])

  const handlePasswordBlur = () => {
    if (!newPassword) {
      setPasswordError('Password is required')
    } else {
      const validation = validatePassword(newPassword)
      if (!validation.valid) {
        setPasswordError(validation.errors[0])
      } else {
        setPasswordError('')
      }
    }
  }

  const handleConfirmPasswordBlur = () => {
    if (!confirmPassword) {
      setConfirmPasswordError('Please confirm your password')
    } else if (newPassword !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match')
    } else {
      setConfirmPasswordError('')
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setGeneralError('')

    if (!token) {
      setGeneralError('Invalid or missing reset token')
      return
    }

    // Validate
    let isValid = true
    if (!newPassword) {
      setPasswordError('Password is required')
      isValid = false
    } else {
      const validation = validatePassword(newPassword)
      if (!validation.valid) {
        setPasswordError(validation.errors[0])
        isValid = false
      }
    }

    if (!confirmPassword) {
      setConfirmPasswordError('Please confirm your password')
      isValid = false
    } else if (newPassword !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match')
      isValid = false
    }

    if (!isValid) return

    setIsLoading(true)
    try {
      await resetPassword(token, newPassword)
      router.push('/login?reset=success')
    } catch (error: any) {
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (detail.includes('expired') || detail.includes('invalid')) {
          setIsTokenValid(false)
          setGeneralError('This reset link has expired or is invalid')
        } else {
          setGeneralError(detail)
        }
      } else {
        setGeneralError('Failed to reset password. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (!isTokenValid) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-4 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <div>
            <p className="font-medium">Invalid Reset Link</p>
            <p className="text-sm">{generalError || 'This reset link is invalid or has expired.'}</p>
          </div>
        </div>
        <Link href="/forgot-password">
          <Button variant="outline" className="w-full">
            Request a new reset link
          </Button>
        </Link>
        <div className="text-center text-sm">
          <Link href="/login" className="text-primary hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {generalError && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {generalError}
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="newPassword" className="text-sm font-medium">
          New Password
        </label>
        <Input
          id="newPassword"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          onBlur={handlePasswordBlur}
          placeholder="Enter your new password"
          disabled={isLoading}
          className={passwordError ? 'border-destructive' : ''}
        />
        {passwordError && (
          <p className="text-sm text-destructive">{passwordError}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Must be at least 8 characters with uppercase, lowercase, and a digit
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="confirmPassword" className="text-sm font-medium">
          Confirm Password
        </label>
        <Input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          onBlur={handleConfirmPasswordBlur}
          placeholder="Confirm your new password"
          disabled={isLoading}
          className={confirmPasswordError ? 'border-destructive' : ''}
        />
        {confirmPasswordError && (
          <p className="text-sm text-destructive">{confirmPasswordError}</p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Resetting...
          </>
        ) : (
          'Reset password'
        )}
      </Button>

      <div className="text-center text-sm">
        <Link href="/login" className="text-primary hover:underline">
          Back to login
        </Link>
      </div>
    </form>
  )
}

