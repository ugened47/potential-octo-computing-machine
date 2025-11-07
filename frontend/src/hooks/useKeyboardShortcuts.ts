'use client'

import { useEffect } from 'react'

interface KeyboardShortcuts {
  [key: string]: () => void
}

export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcuts,
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        (event.target as HTMLElement).isContentEditable
      ) {
        return
      }

      const key = event.key.toLowerCase()
      const modifier = event.shiftKey ? 'shift+' : ''
      const keyCombo = `${modifier}${key}`

      // Check for exact matches first
      if (shortcuts[keyCombo]) {
        event.preventDefault()
        shortcuts[keyCombo]()
        return
      }

      // Check for key without modifier
      if (shortcuts[key]) {
        event.preventDefault()
        shortcuts[key]()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [shortcuts, enabled])
}

