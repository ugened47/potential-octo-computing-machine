'use client'

import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { AlertCircle, RefreshCw } from 'lucide-react'
import type { TranscriptProgress as TranscriptProgressType } from '@/types/transcript'
import { getTranscriptionProgress, triggerTranscription } from '@/lib/transcript-api'

interface TranscriptionProgressProps {
  videoId: string
  onComplete?: () => void
  pollInterval?: number
}

export function TranscriptionProgress({
  videoId,
  onComplete,
  pollInterval = 2000,
}: TranscriptionProgressProps) {
  const [progress, setProgress] = useState<TranscriptProgressType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(true)

  useEffect(() => {
    if (!isPolling) return

    let intervalId: NodeJS.Timeout

    const fetchProgress = async () => {
      try {
        const data = await getTranscriptionProgress(videoId)
        setProgress(data)
        setError(null)

        // Stop polling if completed or failed
        if (data.progress === 100 || data.status.toLowerCase().includes('failed')) {
          setIsPolling(false)
          if (data.progress === 100 && onComplete) {
            onComplete()
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch progress')
        setIsPolling(false)
      }
    }

    // Initial fetch
    fetchProgress()

    // Set up polling
    intervalId = setInterval(fetchProgress, pollInterval)

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [videoId, pollInterval, isPolling, onComplete])

  const handleRetry = async () => {
    try {
      setError(null)
      setIsPolling(true)
      await triggerTranscription(videoId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger transcription')
    }
  }

  if (!progress) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    )
  }

  const isFailed = progress.status.toLowerCase().includes('failed')
  const isCompleted = progress.progress === 100

  return (
    <div className="space-y-4 p-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{progress.status}</span>
          <span className="text-muted-foreground">{progress.progress}%</span>
        </div>
        <Progress value={progress.progress} />
      </div>

      {/* Estimated time remaining */}
      {progress.estimated_time_remaining && !isCompleted && (
        <div className="text-sm text-muted-foreground">
          Estimated time remaining:{' '}
          {Math.ceil(progress.estimated_time_remaining / 60)} minutes
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Failed status with retry */}
      {isFailed && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>Transcription failed: {progress.status}</span>
          </div>
          <Button onClick={handleRetry} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Transcription
          </Button>
        </div>
      )}

      {/* Completed status */}
      {isCompleted && (
        <div className="text-sm text-green-600 dark:text-green-400">
          ✓ Transcription completed successfully
        </div>
      )}
    </div>
  )
}

