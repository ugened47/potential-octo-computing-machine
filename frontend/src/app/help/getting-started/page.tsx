'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Upload, Search, Scissors, Download, CheckCircle2 } from 'lucide-react'

const steps = [
  {
    title: 'Upload Your Video',
    description: 'Start by uploading a video file',
    icon: Upload,
    details: [
      'Click the "Upload Video" button in the header',
      'Select a video file (MP4, MOV, AVI, WebM, or MKV)',
      'Maximum file size is 2GB',
      'Add a title and description (optional)',
      'Wait for upload to complete',
    ],
  },
  {
    title: 'Wait for Processing',
    description: 'Your video will be automatically processed',
    icon: Search,
    details: [
      'Video metadata is extracted automatically',
      'Transcription begins automatically after upload',
      'Processing typically takes 5 minutes for a 30-minute video',
      'You can monitor progress on the dashboard',
      'You\'ll be notified when processing is complete',
    ],
  },
  {
    title: 'Edit and Create Clips',
    description: 'Use AI-powered tools to find highlights',
    icon: Scissors,
    details: [
      'Search transcript using keywords',
      'Select moments to create clips',
      'Use the timeline editor to fine-tune segments',
      'Remove silence automatically',
      'Preview clips before exporting',
    ],
  },
  {
    title: 'Export Your Content',
    description: 'Download your edited videos',
    icon: Download,
    details: [
      'Select clips or segments to export',
      'Choose quality settings (720p or 1080p)',
      'Export videos in MP4 format',
      'Download transcripts as SRT or VTT files',
      'Share your content easily',
    ],
  },
]

export default function GettingStartedPage() {
  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-8">
        <Link href="/help">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Help
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">Getting Started</h1>
        <p className="text-muted-foreground">
          Learn how to use AI Video Editor in just a few simple steps.
        </p>
      </div>

      <div className="space-y-8">
        {steps.map((step, index) => {
          const Icon = step.icon
          return (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold text-muted-foreground">
                        Step {index + 1}
                      </span>
                    </div>
                    <CardTitle>{step.title}</CardTitle>
                    <CardDescription className="mt-1">{step.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {step.details.map((detail, detailIndex) => (
                    <li key={detailIndex} className="flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{detail}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Ready to Get Started?</CardTitle>
            <CardDescription>
              Upload your first video and start creating amazing content.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/upload">
              <Button>Upload Your First Video</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

