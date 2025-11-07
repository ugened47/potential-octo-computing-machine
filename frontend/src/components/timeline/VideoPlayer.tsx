'use client'

import { useEffect, useRef, useState } from 'react'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import type Player from 'video.js/dist/types/player'

interface VideoPlayerProps {
  videoUrl: string
  currentTime?: number
  playbackRate?: number
  onTimeUpdate?: (time: number) => void
  onSeek?: (time: number) => void
  onDurationChange?: (duration: number) => void
  onPlay?: () => void
  onPause?: () => void
  className?: string
}

export function VideoPlayer({
  videoUrl,
  currentTime = 0,
  playbackRate = 1.0,
  onTimeUpdate,
  onSeek,
  onDurationChange,
  onPlay,
  onPause,
  className = '',
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<Player | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    if (!videoRef.current) return

    // Initialize Video.js player
    const player = videojs(videoRef.current, {
      controls: true,
      responsive: true,
      fluid: false,
      playbackRates: [0.5, 1, 1.5, 2],
      html5: {
        vhs: {
          overrideNative: true,
        },
        nativeVideoTracks: false,
        nativeAudioTracks: false,
        nativeTextTracks: false,
      },
    })

    playerRef.current = player

    // Handle time updates
    const handleTimeUpdate = () => {
      if (onTimeUpdate && player.currentTime() !== null) {
        onTimeUpdate(player.currentTime())
      }
    }

    // Handle duration change
    const handleDurationChange = () => {
      if (onDurationChange && player.duration() !== null) {
        onDurationChange(player.duration())
      }
    }

    // Handle play
    const handlePlay = () => {
      if (onPlay) {
        onPlay()
      }
    }

    // Handle pause
    const handlePause = () => {
      if (onPause) {
        onPause()
      }
    }

    // Handle seek
    const handleSeeked = () => {
      if (onSeek && player.currentTime() !== null) {
        onSeek(player.currentTime())
      }
    }

    player.on('timeupdate', handleTimeUpdate)
    player.on('loadedmetadata', handleDurationChange)
    player.on('durationchange', handleDurationChange)
    player.on('play', handlePlay)
    player.on('pause', handlePause)
    player.on('seeked', handleSeeked)
    player.on('ready', () => {
      setIsReady(true)
    })

    // Set initial playback rate
    if (playbackRate !== 1.0) {
      player.playbackRate(playbackRate)
    }

    return () => {
      if (playerRef.current) {
        playerRef.current.dispose()
        playerRef.current = null
      }
    }
  }, [videoUrl, onTimeUpdate, onDurationChange, onPlay, onPause, onSeek, playbackRate])

  // Sync currentTime prop with player
  useEffect(() => {
    if (!playerRef.current || !isReady) return

    const player = playerRef.current
    const currentPlayerTime = player.currentTime()

    // Only seek if there's a significant difference (avoid infinite loops)
    if (currentPlayerTime !== null && Math.abs(currentPlayerTime - currentTime) > 0.1) {
      player.currentTime(currentTime)
    }
  }, [currentTime, isReady])

  // Sync playback rate
  useEffect(() => {
    if (!playerRef.current || !isReady) return
    playerRef.current.playbackRate(playbackRate)
  }, [playbackRate, isReady])

  return (
    <div className={className}>
      <div data-vjs-player>
        <video
          ref={videoRef}
          className="video-js vjs-big-play-centered"
          playsInline
        >
          <source src={videoUrl} type="video/mp4" />
          <p className="vjs-no-js">
            To view this video please enable JavaScript, and consider upgrading to a
            web browser that{' '}
            <a href="https://videojs.com/html5-video-support/" target="_blank">
              supports HTML5 video
            </a>
            .
          </p>
        </video>
      </div>
    </div>
  )
}

