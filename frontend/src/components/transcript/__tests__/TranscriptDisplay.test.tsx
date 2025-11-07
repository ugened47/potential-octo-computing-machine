import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TranscriptDisplay } from '../TranscriptDisplay'
import type { Transcript } from '@/types/transcript'

const mockTranscript: Transcript = {
  id: '1',
  video_id: 'video-1',
  full_text: 'Hello world',
  word_timestamps: {
    words: [
      { word: 'Hello', start: 0.0, end: 0.5, confidence: 0.95 },
      { word: 'world', start: 0.5, end: 1.0, confidence: 0.92 },
    ],
  },
  language: 'en',
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('TranscriptDisplay', () => {
  it('renders transcript words', () => {
    render(<TranscriptDisplay transcript={mockTranscript} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('world')).toBeInTheDocument()
  })

  it('highlights current word based on currentTime', () => {
    const { container } = render(
      <TranscriptDisplay transcript={mockTranscript} currentTime={0.3} />
    )
    const highlightedWord = container.querySelector('.bg-primary')
    expect(highlightedWord).toBeInTheDocument()
  })

  it('calls onWordClick when word is clicked', () => {
    const handleWordClick = vi.fn()
    render(
      <TranscriptDisplay
        transcript={mockTranscript}
        onWordClick={handleWordClick}
      />
    )
    const helloWord = screen.getByText('Hello')
    helloWord.click()
    expect(handleWordClick).toHaveBeenCalledWith(0.0)
  })

  it('highlights search matches', () => {
    const { container } = render(
      <TranscriptDisplay transcript={mockTranscript} searchQuery="Hello" />
    )
    const match = container.querySelector('.bg-yellow-200, .dark\\:bg-yellow-900')
    expect(match).toBeInTheDocument()
  })

  it('displays language and status', () => {
    render(<TranscriptDisplay transcript={mockTranscript} />)
    expect(screen.getByText(/Language: EN/i)).toBeInTheDocument()
    expect(screen.getByText(/Status: completed/i)).toBeInTheDocument()
  })
})

