'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Download } from 'lucide-react'
import { exportTranscript, downloadTranscript } from '@/lib/transcript-api'

interface TranscriptExportProps {
  videoId: string
  className?: string
}

export function TranscriptExport({ videoId, className }: TranscriptExportProps) {
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async (format: 'srt' | 'vtt') => {
    try {
      setIsExporting(true)
      const blob = await exportTranscript(videoId, format)
      const filename = `transcript_${videoId}.${format}`
      downloadTranscript(blob, filename)
    } catch (error) {
      console.error(`Failed to export transcript as ${format}:`, error)
      alert(`Failed to export transcript. Please try again.`)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className={className}>
      <div className="flex gap-2">
        <Button
          onClick={() => handleExport('srt')}
          disabled={isExporting}
          variant="outline"
          size="sm"
        >
          <Download className="mr-2 h-4 w-4" />
          Export SRT
        </Button>
        <Button
          onClick={() => handleExport('vtt')}
          disabled={isExporting}
          variant="outline"
          size="sm"
        >
          <Download className="mr-2 h-4 w-4" />
          Export VTT
        </Button>
      </div>
    </div>
  )
}

