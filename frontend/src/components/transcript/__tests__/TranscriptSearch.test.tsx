import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TranscriptSearch } from '../TranscriptSearch'

describe('TranscriptSearch', () => {
  it('renders search input', () => {
    const onSearchChange = vi.fn()
    render(<TranscriptSearch onSearchChange={onSearchChange} />)
    expect(screen.getByPlaceholderText(/search transcript/i)).toBeInTheDocument()
  })

  it('calls onSearchChange when typing', async () => {
    const user = userEvent.setup()
    const onSearchChange = vi.fn()
    render(<TranscriptSearch onSearchChange={onSearchChange} />)
    
    const input = screen.getByPlaceholderText(/search transcript/i)
    await user.type(input, 'test')
    
    expect(onSearchChange).toHaveBeenCalledWith('test')
  })

  it('shows clear button when there is text', async () => {
    const user = userEvent.setup()
    const onSearchChange = vi.fn()
    render(<TranscriptSearch onSearchChange={onSearchChange} />)
    
    const input = screen.getByPlaceholderText(/search transcript/i)
    await user.type(input, 'test')
    
    const clearButton = screen.getByRole('button')
    expect(clearButton).toBeInTheDocument()
  })

  it('clears search when clear button is clicked', async () => {
    const user = userEvent.setup()
    const onSearchChange = vi.fn()
    render(<TranscriptSearch onSearchChange={onSearchChange} />)
    
    const input = screen.getByPlaceholderText(/search transcript/i)
    await user.type(input, 'test')
    
    const clearButton = screen.getByRole('button')
    await user.click(clearButton)
    
    expect(onSearchChange).toHaveBeenCalledWith('')
    expect(input).toHaveValue('')
  })
})

