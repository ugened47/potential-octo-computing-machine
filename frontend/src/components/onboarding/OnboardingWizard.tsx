'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { OnboardingStep } from './OnboardingStep'
import { useOnboarding } from '@/store/onboarding-store'
import { Video, Search, Scissors, Download } from 'lucide-react'

const steps = [
  {
    title: 'Welcome to AI Video Editor',
    description: 'Let\'s get you started with a quick tour of the platform.',
    content: (
      <div className="space-y-4">
        <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
          <Video className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">Upload Your Videos</h3>
            <p className="text-sm text-muted-foreground">
              Upload videos up to 2GB in MP4, MOV, AVI, WebM, or MKV format.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
          <Search className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">AI-Powered Transcription</h3>
            <p className="text-sm text-muted-foreground">
              Automatically transcribe your videos with word-level timestamps.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
          <Scissors className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">Smart Clipping</h3>
            <p className="text-sm text-muted-foreground">
              Find highlights using keyword search and create clips automatically.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
          <Download className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">Export & Share</h3>
            <p className="text-sm text-muted-foreground">
              Export your edited videos in high quality and share them easily.
            </p>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'Upload Your First Video',
    description: 'Start by uploading a video to get started.',
    content: (
      <div className="space-y-4">
        <div className="p-6 border-2 border-dashed rounded-lg text-center">
          <Video className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="font-semibold mb-2">Ready to upload?</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Click the "Upload Video" button in the header to get started.
          </p>
        </div>
        <div className="text-sm text-muted-foreground space-y-2">
          <p>• Supported formats: MP4, MOV, AVI, WebM, MKV</p>
          <p>• Maximum file size: 2GB</p>
          <p>• Processing time: ~5 minutes for a 30-minute video</p>
        </div>
      </div>
    ),
  },
  {
    title: 'Explore the Dashboard',
    description: 'Your dashboard is where you manage all your videos.',
    content: (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg">
            <h4 className="font-semibold mb-2">Video Library</h4>
            <p className="text-sm text-muted-foreground">
              View all your uploaded videos in grid or list view.
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <h4 className="font-semibold mb-2">Statistics</h4>
            <p className="text-sm text-muted-foreground">
              Track your storage usage and processing time.
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <h4 className="font-semibold mb-2">Search & Filter</h4>
            <p className="text-sm text-muted-foreground">
              Find videos quickly using search and status filters.
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <h4 className="font-semibold mb-2">Processing Queue</h4>
            <p className="text-sm text-muted-foreground">
              Monitor videos currently being processed.
            </p>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'You\'re All Set!',
    description: 'Start creating amazing video content with AI-powered tools.',
    content: (
      <div className="space-y-4 text-center">
        <div className="p-8">
          <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
            <Video className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Ready to get started?</h3>
          <p className="text-muted-foreground">
            Upload your first video and let AI do the heavy lifting for you.
          </p>
        </div>
      </div>
    ),
  },
]

export function OnboardingWizard() {
  const router = useRouter()
  const { currentStep, completeStep, skipOnboarding, setCurrentStep } = useOnboarding()

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      completeStep(currentStep)
    } else {
      completeStep(currentStep)
      router.push('/dashboard')
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    skipOnboarding()
    router.push('/dashboard')
  }

  const currentStepData = steps[currentStep]

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <OnboardingStep
        title={currentStepData.title}
        description={currentStepData.description}
        step={currentStep}
        totalSteps={steps.length}
        onNext={handleNext}
        onPrevious={handlePrevious}
        onSkip={handleSkip}
        isFirst={currentStep === 0}
        isLast={currentStep === steps.length - 1}
      >
        {currentStepData.content}
      </OnboardingStep>
    </div>
  )
}

