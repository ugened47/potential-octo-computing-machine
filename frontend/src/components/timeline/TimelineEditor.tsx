'use client'

import { useEffect, useRef, useState } from 'react'
import { Stage, Layer, Rect, Line, Group, Text } from 'react-konva'
import type { Segment } from '@/types/timeline'

interface TimelineEditorProps {
  duration: number
  currentTime: number
  segments: Segment[]
  zoomLevel: number
  onSeek: (time: number) => void
  onSegmentClick?: (segmentId: string) => void
  onSegmentDrag?: (segmentId: string, startTime: number, endTime: number) => void
  className?: string
}

export function TimelineEditor({
  duration,
  currentTime,
  segments,
  zoomLevel,
  onSeek,
  onSegmentClick,
  onSegmentDrag,
  className = '',
}: TimelineEditorProps) {
  const stageRef = useRef<any>(null)
  const [width, setWidth] = useState(800)
  const [height, setHeight] = useState(120)

  useEffect(() => {
    const updateSize = () => {
      if (stageRef.current) {
        const container = stageRef.current.container()
        if (container) {
          setWidth(container.offsetWidth || 800)
        }
      }
    }

    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  const pixelsPerSecond = (width / duration) * zoomLevel
  const playheadX = currentTime * pixelsPerSecond

  const handleStageClick = (e: any) => {
    const stage = e.target.getStage()
    const pointerPos = stage.getPointerPosition()
    const clickedTime = (pointerPos.x / pixelsPerSecond) * zoomLevel
    const clampedTime = Math.max(0, Math.min(clickedTime, duration))
    onSeek(clampedTime)
  }

  return (
    <div className={`w-full ${className}`}>
      <Stage
        ref={stageRef}
        width={width}
        height={height}
        onClick={handleStageClick}
        className="cursor-pointer"
      >
        <Layer>
          {/* Background */}
          <Rect x={0} y={0} width={width} height={height} fill="#1e293b" />

          {/* Time markers */}
          {Array.from({ length: Math.floor(duration) + 1 }).map((_, i) => {
            const x = (i / duration) * width * zoomLevel
            if (x > width) return null
            return (
              <Group key={i}>
                <Line
                  points={[x, height - 20, x, height]}
                  stroke="#64748b"
                  strokeWidth={1}
                />
                <Text
                  x={x + 2}
                  y={height - 18}
                  text={`${i}s`}
                  fontSize={10}
                  fill="#94a3b8"
                />
              </Group>
            )
          })}

          {/* Segments */}
          {segments.map((segment) => {
            const segmentStartX = (segment.start_time / duration) * width * zoomLevel
            const segmentEndX = (segment.end_time / duration) * width * zoomLevel
            const segmentWidth = segmentEndX - segmentStartX

            return (
              <Group
                key={segment.id}
                x={segmentStartX}
                y={20}
                draggable
                onDragEnd={(e) => {
                  const newStartX = Math.max(0, e.target.x())
                  const newStartTime = (newStartX / pixelsPerSecond) * zoomLevel
                  const segmentDuration = segment.end_time - segment.start_time
                  const newEndTime = Math.min(
                    duration,
                    newStartTime + segmentDuration
                  )
                  if (onSegmentDrag) {
                    onSegmentDrag(segment.id, newStartTime, newEndTime)
                  }
                }}
                onClick={() => {
                  if (onSegmentClick) {
                    onSegmentClick(segment.id)
                  }
                }}
              >
                <Rect
                  width={segmentWidth}
                  height={60}
                  fill={segment.selected ? '#3b82f6' : '#475569'}
                  stroke="#64748b"
                  strokeWidth={1}
                  cornerRadius={4}
                />
                <Text
                  x={4}
                  y={20}
                  text={`${segment.start_time.toFixed(1)}s - ${segment.end_time.toFixed(1)}s`}
                  fontSize={10}
                  fill="#ffffff"
                />
              </Group>
            )
          })}

          {/* Playhead */}
          <Line
            points={[playheadX, 0, playheadX, height]}
            stroke="#ef4444"
            strokeWidth={2}
            lineCap="round"
          />
        </Layer>
      </Stage>
    </div>
  )
}

