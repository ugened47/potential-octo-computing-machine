'use client'

import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import type { WaveformData } from '@/types/timeline'

interface WaveformDisplayProps {
  waveformData: WaveformData
  currentTime?: number
  onSeek?: (time: number) => void
  className?: string
}

export function WaveformDisplay({
  waveformData,
  currentTime = 0,
  onSeek,
  className = '',
}: WaveformDisplayProps) {
  const waveformRef = useRef<HTMLDivElement | null>(null)
  const wavesurferRef = useRef<WaveSurfer | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    if (!waveformRef.current || !waveformData) return

    // Initialize WaveSurfer
    const wavesurfer = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#94a3b8',
      progressColor: '#3b82f6',
      cursorColor: '#ef4444',
      barWidth: 2,
      barRadius: 1,
      responsive: true,
      height: 100,
      normalize: true,
      backend: 'WebAudio',
      mediaControls: false,
    })

    wavesurferRef.current = wavesurfer

    // Load waveform data
    wavesurfer.load('', waveformData.peaks, waveformData.sample_rate)

    // Handle seek
    const handleSeek = () => {
      if (onSeek && wavesurfer.getCurrentTime() !== null) {
        onSeek(wavesurfer.getCurrentTime())
      }
    }

    wavesurfer.on('ready', () => {
      setIsReady(true)
    })

    wavesurfer.on('seek', handleSeek)
    wavesurfer.on('interaction', handleSeek)

    return () => {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy()
        wavesurferRef.current = null
      }
    }
  }, [waveformData, onSeek])

  // Sync currentTime with waveform
  useEffect(() => {
    if (!wavesurferRef.current || !isReady) return

    const wavesurfer = wavesurferRef.current
    const currentWaveformTime = wavesurfer.getCurrentTime()

    // Only seek if there's a significant difference
    if (Math.abs(currentWaveformTime - currentTime) > 0.1) {
      wavesurfer.seekTo(currentTime / waveformData.duration)
    }
  }, [currentTime, waveformData.duration, isReady])

  return (
    <div className={`w-full ${className}`}>
      <div ref={waveformRef} className="w-full" />
    </div>
  )
}

