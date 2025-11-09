'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { VideoPlayer } from './VideoPlayer'
import { WaveformDisplay } from './WaveformDisplay'
import { TimelineEditor } from './TimelineEditor'
import { TimelineControls } from './TimelineControls'
import { TranscriptPanel } from '@/components/transcript/TranscriptPanel'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import {
  getWaveform,
  generateWaveform,
  getWaveformStatus,
  saveSegments,
  getSegments,
} from '@/lib/timeline-api'
import { getVideoPlaybackUrl } from '@/lib/video-api'
import type { WaveformData, Segment } from '@/types/timeline'
import type { Video } from '@/types/video'

interface VideoEditorProps {
  video: Video
  className?: string
}

export function VideoEditor({ video, className = '' }: VideoEditorProps) {
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [waveformData, setWaveformData] = useState<WaveformData | null>(null)
  const [isLoadingWaveform, setIsLoadingWaveform] = useState(true)
  const [isGeneratingWaveform, setIsGeneratingWaveform] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(video.duration || 0)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [segments, setSegments] = useState<Segment[]>([])
  const [isSavingSegments, setIsSavingSegments] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)
  const autosaveTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Load video playback URL
  useEffect(() => {
    const loadVideoUrl = async () => {
      try {
        const url = await getVideoPlaybackUrl(video.id)
        setVideoUrl(url)
      } catch (error) {
        console.error('Failed to load video URL:', error)
      }
    }

    if (video.id) {
      loadVideoUrl()
    }
  }, [video.id])

  // Load waveform data
  useEffect(() => {
    const loadWaveform = async () => {
      try {
        setIsLoadingWaveform(true)
        const data = await getWaveform(video.id)
        setWaveformData(data)
      } catch (error: any) {
        // Waveform doesn't exist, try to generate it
        if (error.status === 404 || error.response?.status === 404) {
          try {
            setIsGeneratingWaveform(true)
            await generateWaveform(video.id)
            // Poll for waveform status
            const pollWaveform = async () => {
              const maxAttempts = 30
              let attempts = 0
              const interval = setInterval(async () => {
                attempts++
                try {
                  const status = await getWaveformStatus(video.id)
                  if (status.status === 'completed') {
                    const data = await getWaveform(video.id)
                    setWaveformData(data)
                    setIsGeneratingWaveform(false)
                    clearInterval(interval)
                  } else if (status.status === 'failed' || attempts >= maxAttempts) {
                    setIsGeneratingWaveform(false)
                    clearInterval(interval)
                  }
                } catch (err) {
                  // Continue polling
                }
              }, 2000)

              setTimeout(() => {
                clearInterval(interval)
                setIsGeneratingWaveform(false)
              }, 60000) // Timeout after 60 seconds
            }
            pollWaveform()
          } catch (genError) {
            console.error('Failed to generate waveform:', genError)
            setIsGeneratingWaveform(false)
          }
        } else {
          console.error('Failed to load waveform:', error)
        }
      } finally {
        setIsLoadingWaveform(false)
      }
    }

    if (video.id && video.duration) {
      loadWaveform()
    }
  }, [video.id, video.duration])

  // Load saved segments
  useEffect(() => {
    const loadSegments = async () => {
      try {
        const savedSegments = await getSegments(video.id)
        if (savedSegments && savedSegments.length > 0) {
          setSegments(savedSegments)
        }
      } catch (error) {
        console.error('Failed to load segments:', error)
      }
    }

    if (video.id) {
      loadSegments()
    }
  }, [video.id])

  // Autosave segments every 30 seconds
  useEffect(() => {
    const saveSegmentsToServer = async () => {
      if (segments.length === 0) return

      try {
        setIsSavingSegments(true)
        await saveSegments(video.id, segments)
        setLastSavedAt(new Date())
      } catch (error) {
        console.error('Failed to autosave segments:', error)
      } finally {
        setIsSavingSegments(false)
      }
    }

    // Clear existing timer
    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current)
    }

    // Set new timer for 30 seconds
    autosaveTimerRef.current = setTimeout(() => {
      saveSegmentsToServer()
    }, 30000)

    // Cleanup on unmount
    return () => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current)
      }
    }
  }, [segments, video.id])

  // Save segments before unmount
  useEffect(() => {
    return () => {
      // Save segments on unmount if there are any
      if (segments.length > 0) {
        saveSegments(video.id, segments).catch((error) => {
          console.error('Failed to save segments on unmount:', error)
        })
      }
    }
  }, [segments, video.id])

  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev)
  }, [])

  const handleSeek = useCallback((time: number) => {
    setCurrentTime(Math.max(0, Math.min(time, duration)))
  }, [duration])

  const handleSeekBackward = useCallback((seconds: number) => {
    setCurrentTime((prev) => Math.max(0, prev - seconds))
  }, [])

  const handleSeekForward = useCallback((seconds: number) => {
    setCurrentTime((prev) => Math.min(duration, prev + seconds))
  }, [])

  const handleZoomIn = useCallback(() => {
    setZoomLevel((prev) => Math.min(10, prev * 1.2))
  }, [])

  const handleZoomOut = useCallback(() => {
    setZoomLevel((prev) => Math.max(1, prev / 1.2))
  }, [])

  const handleResetZoom = useCallback(() => {
    setZoomLevel(1)
  }, [])

  const handleSegmentClick = useCallback((segmentId: string) => {
    setSegments((prev) =>
      prev.map((seg) =>
        seg.id === segmentId ? { ...seg, selected: !seg.selected } : seg
      )
    )
  }, [])

  const handleSegmentDrag = useCallback(
    (segmentId: string, startTime: number, endTime: number) => {
      setSegments((prev) =>
        prev.map((seg) =>
          seg.id === segmentId
            ? { ...seg, start_time: startTime, end_time: endTime }
            : seg
        )
      )
    },
    []
  )

  // Keyboard shortcuts
  useKeyboardShortcuts(
    {
      ' ': handlePlayPause,
      'arrowleft': () => handleSeekBackward(1),
      'shift+arrowleft': () => handleSeekBackward(5),
      'arrowright': () => handleSeekForward(1),
      'shift+arrowright': () => handleSeekForward(5),
      '+': handleZoomIn,
      '-': handleZoomOut,
      '0': handleResetZoom,
    },
    true
  )

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Video Player */}
      <div className="w-full bg-black">
        {videoUrl ? (
          <VideoPlayer
            videoUrl={videoUrl}
            currentTime={currentTime}
            playbackRate={playbackRate}
            onTimeUpdate={setCurrentTime}
            onSeek={handleSeek}
            onDurationChange={setDuration}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            className="w-full"
          />
        ) : (
          <div className="aspect-video flex items-center justify-center text-muted-foreground">
            Loading video...
          </div>
        )}
      </div>

      {/* Timeline Controls */}
      <div className="relative">
        <TimelineControls
          isPlaying={isPlaying}
          currentTime={currentTime}
          duration={duration}
          playbackRate={playbackRate}
          zoomLevel={zoomLevel}
          onPlayPause={handlePlayPause}
          onSeek={handleSeek}
          onSeekBackward={handleSeekBackward}
          onSeekForward={handleSeekForward}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetZoom={handleResetZoom}
          onPlaybackRateChange={setPlaybackRate}
        />
        {/* Autosave indicator */}
        {segments.length > 0 && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
            {isSavingSegments ? (
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500"></span>
                Saving...
              </span>
            ) : lastSavedAt ? (
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-2 rounded-full bg-green-500"></span>
                Saved {new Date(lastSavedAt).toLocaleTimeString()}
              </span>
            ) : null}
          </div>
        )}
      </div>

      {/* Waveform */}
      {isLoadingWaveform || isGeneratingWaveform ? (
        <div className="h-24 flex items-center justify-center text-sm text-muted-foreground">
          {isGeneratingWaveform ? 'Generating waveform...' : 'Loading waveform...'}
        </div>
      ) : waveformData ? (
        <WaveformDisplay
          waveformData={waveformData}
          currentTime={currentTime}
          onSeek={handleSeek}
          className="h-24 border-t"
        />
      ) : null}

      {/* Timeline Editor */}
      {duration > 0 && (
        <TimelineEditor
          duration={duration}
          currentTime={currentTime}
          segments={segments}
          zoomLevel={zoomLevel}
          onSeek={handleSeek}
          onSegmentClick={handleSegmentClick}
          onSegmentDrag={handleSegmentDrag}
          className="border-t"
        />
      )}

      {/* Transcript Panel */}
      <div className="flex-1 min-h-0 border-t">
        <TranscriptPanel
          videoId={video.id}
          currentTime={currentTime}
          onSeek={handleSeek}
        />
      </div>
    </div>
  )
}

