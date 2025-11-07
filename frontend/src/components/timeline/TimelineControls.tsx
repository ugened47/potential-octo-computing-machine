'use client'

import { Play, Pause, SkipBack, SkipForward, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TimelineControlsProps {
  isPlaying: boolean
  currentTime: number
  duration: number
  playbackRate: number
  zoomLevel: number
  onPlayPause: () => void
  onSeek: (time: number) => void
  onSeekBackward: (seconds: number) => void
  onSeekForward: (seconds: number) => void
  onZoomIn: () => void
  onZoomOut: () => void
  onResetZoom: () => void
  onPlaybackRateChange: (rate: number) => void
  className?: string
}

export function TimelineControls({
  isPlaying,
  currentTime,
  duration,
  playbackRate,
  zoomLevel,
  onPlayPause,
  onSeek,
  onSeekBackward,
  onSeekForward,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  onPlaybackRateChange,
  className = '',
}: TimelineControlsProps) {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={`flex items-center gap-2 p-2 border-t ${className}`}>
      {/* Playback controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onSeekBackward(5)}
          title="Seek backward 5s"
        >
          <SkipBack className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onSeekBackward(1)}
          title="Seek backward 1s"
        >
          <SkipBack className="h-3 w-3" />
        </Button>
        <Button
          variant="default"
          size="icon"
          onClick={onPlayPause}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onSeekForward(1)}
          title="Seek forward 1s"
        >
          <SkipForward className="h-3 w-3" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onSeekForward(5)}
          title="Seek forward 5s"
        >
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      {/* Time display */}
      <div className="flex items-center gap-2 px-2 text-sm font-mono">
        <span>{formatTime(currentTime)}</span>
        <span className="text-muted-foreground">/</span>
        <span className="text-muted-foreground">{formatTime(duration)}</span>
      </div>

      {/* Playback rate */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-muted-foreground">Speed:</span>
        <select
          value={playbackRate}
          onChange={(e) => onPlaybackRateChange(parseFloat(e.target.value))}
          className="h-8 rounded-md border border-input bg-background px-2 text-xs"
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>

      {/* Zoom controls */}
      <div className="flex items-center gap-1 ml-auto">
        <Button
          variant="outline"
          size="icon"
          onClick={onZoomOut}
          title="Zoom out"
          disabled={zoomLevel <= 1}
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-xs text-muted-foreground px-2">
          {Math.round(zoomLevel * 100)}%
        </span>
        <Button
          variant="outline"
          size="icon"
          onClick={onZoomIn}
          title="Zoom in"
          disabled={zoomLevel >= 10}
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={onResetZoom}
          title="Reset zoom"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

