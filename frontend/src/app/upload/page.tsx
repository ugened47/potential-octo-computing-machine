'use client'

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { UploadProgress, type UploadStatus } from '@/components/video/UploadProgress'
import { Upload, FileVideo, X } from 'lucide-react'
import {
  getPresignedUrl,
  uploadToS3,
  createVideoRecord,
} from '@/lib/video-api'
import {
  validateVideoFormat,
  validateVideoSize,
  getVideoMimeType,
} from '@/lib/validation'
import { formatFileSize } from '@/lib/utils'

const MAX_FILE_SIZE_MB = 2048 // 2GB

export default function UploadPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadXhrRef = useRef<XMLHttpRequest | null>(null)

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('preparing')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSpeed, setUploadSpeed] = useState(0)
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number>()
  const [error, setError] = useState<string | null>(null)
  const [videoId, setVideoId] = useState<string | null>(null)

  const validateFile = (fileToValidate: File): string | null => {
    if (!validateVideoFormat(fileToValidate.name)) {
      return 'Invalid file format. Allowed formats: MP4, MOV, AVI, WebM, MKV'
    }
    if (!validateVideoSize(fileToValidate.size, MAX_FILE_SIZE_MB)) {
      return `File size exceeds ${MAX_FILE_SIZE_MB}MB limit`
    }
    return null
  }

  const handleFileSelect = (selectedFile: File) => {
    const validationError = validateFile(selectedFile)
    if (validationError) {
      setError(validationError)
      return
    }

    setFile(selectedFile)
    setTitle(selectedFile.name.replace(/\.[^/.]+$/, '')) // Remove extension
    setError(null)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }, [])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const calculateUploadSpeed = (
    loaded: number,
    total: number,
    startTime: number
  ) => {
    const elapsed = (Date.now() - startTime) / 1000 // seconds
    const speedMBps = loaded / (1024 * 1024) / elapsed
    setUploadSpeed(speedMBps)

    if (speedMBps > 0) {
      const remaining = total - loaded
      const estimatedSeconds = remaining / (1024 * 1024) / speedMBps
      setEstimatedTimeRemaining(estimatedSeconds)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setError(null)
    setUploadStatus('preparing')
    setUploadProgress(0)

    try {
      // Step 1: Get presigned URL
      const presignedResponse = await getPresignedUrl({
        filename: file.name,
        file_size: file.size,
        content_type: getVideoMimeType(file.name),
      })

      setVideoId(presignedResponse.video_id)
      setUploadStatus('uploading')

      // Step 2: Upload to S3
      const uploadStartTime = Date.now()
      await uploadToS3(
        presignedResponse.presigned_url,
        file,
        (progress) => {
          setUploadProgress(progress)
          calculateUploadSpeed(
            (progress / 100) * file.size,
            file.size,
            uploadStartTime
          )
        },
        uploadXhrRef
      )

      setUploadStatus('processing')
      setUploadProgress(100)

      // Step 3: Create video record
      await createVideoRecord({
        video_id: presignedResponse.video_id,
        title: title || file.name.replace(/\.[^/.]+$/, ''),
        description: description || null,
        s3_key: presignedResponse.s3_key,
      })

      setUploadStatus('complete')

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    } catch (err) {
      setUploadStatus('error')
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  const handleCancel = () => {
    if (uploadXhrRef.current) {
      uploadXhrRef.current.abort()
      uploadXhrRef.current = null
    }
    setUploadStatus('preparing')
    setUploadProgress(0)
    setError('Upload cancelled')
  }

  const handleRetry = () => {
    setError(null)
    setUploadStatus('preparing')
    setUploadProgress(0)
    handleUpload()
  }

  const handleReset = () => {
    setFile(null)
    setTitle('')
    setDescription('')
    setUploadStatus('preparing')
    setUploadProgress(0)
    setError(null)
    setVideoId(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 max-w-4xl">
        <h1 className="text-3xl font-bold mb-8">Upload Video</h1>

        {/* Drag and drop zone */}
        {!file && (
          <Card
            className={`border-2 border-dashed transition-colors ${
              isDragging
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <CardContent className="flex flex-col items-center justify-center p-12">
              <Upload className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                Drag and drop your video here
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse
              </p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
              >
                Select File
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileInputChange}
                className="hidden"
              />
              <p className="text-xs text-muted-foreground mt-4">
                Supported formats: MP4, MOV, AVI, WebM, MKV (max {MAX_FILE_SIZE_MB}MB)
              </p>
            </CardContent>
          </Card>
        )}

        {/* File selected view */}
        {file && uploadStatus === 'preparing' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>File Ready</CardTitle>
                <Button variant="ghost" size="icon" onClick={handleReset}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-muted rounded-lg">
                <FileVideo className="h-8 w-8 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(file.size)} • {file.type || 'Unknown type'}
                  </p>
                </div>
                <Badge variant="outline">{file.name.split('.').pop()?.toUpperCase()}</Badge>
              </div>

              <div className="space-y-2">
                <label htmlFor="title" className="text-sm font-medium">
                  Title
                </label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter video title"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="description" className="text-sm font-medium">
                  Description (optional)
                </label>
                <Input
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter video description"
                />
              </div>

              {error && (
                <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
                  {error}
                </div>
              )}

              <Button onClick={handleUpload} className="w-full" size="lg">
                <Upload className="mr-2 h-4 w-4" />
                Upload Video
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Upload progress */}
        {(uploadStatus === 'uploading' ||
          uploadStatus === 'processing' ||
          uploadStatus === 'complete' ||
          uploadStatus === 'error') && (
          <Card>
            <CardHeader>
              <CardTitle>Upload Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <UploadProgress
                progress={uploadProgress}
                status={uploadStatus}
                uploadSpeed={uploadSpeed}
                estimatedTimeRemaining={estimatedTimeRemaining}
                error={error}
                onRetry={handleRetry}
                onCancel={handleCancel}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  )
}

