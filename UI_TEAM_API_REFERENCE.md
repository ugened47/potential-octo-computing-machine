# API Reference for UI Team

**Document Version:** 1.0
**Last Updated:** 2025-11-09
**For:** Frontend Development Team

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Transcription API](#transcription-api)
4. [Silence Removal API](#silence-removal-api)
5. [Error Handling](#error-handling)
6. [UI/UX Best Practices](#uiux-best-practices)
7. [Code Examples](#code-examples)

---

## Overview

This document provides complete API reference for integrating video transcription and silence removal features into the frontend. All endpoints require authentication and follow REST principles.

**Base URL:** `http://localhost:8000/api` (development)

---

## Authentication

All endpoints require a JWT bearer token in the Authorization header.

### Header Format
```http
Authorization: Bearer {your_jwt_token}
```

### Error Responses
- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Valid token but insufficient permissions

---

## Transcription API

### 1. Get Transcript

Retrieve the transcript for a video.

**Endpoint:** `GET /videos/{video_id}/transcript`

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "video_id": "123e4567-e89b-12d3-a456-426614174001",
  "full_text": "Hello, this is a test video. Today we'll discuss...",
  "word_timestamps": {
    "words": [
      {
        "word": "Hello",
        "start": 0.0,
        "end": 0.5,
        "confidence": 0.95
      },
      {
        "word": "this",
        "start": 0.6,
        "end": 0.8,
        "confidence": 0.92
      }
    ]
  },
  "language": "en",
  "status": "completed",
  "accuracy_score": 0.92,
  "created_at": "2025-11-09T12:00:00Z",
  "updated_at": "2025-11-09T12:05:00Z",
  "completed_at": "2025-11-09T12:05:00Z"
}
```

**Error Responses:**
- **404 Not Found:** Video or transcript doesn't exist
- **403 Forbidden:** User doesn't own the video

**UI Integration:**
```typescript
interface Transcript {
  id: string;
  video_id: string;
  full_text: string;
  word_timestamps: {
    words: Array<{
      word: string;
      start: number;
      end: number;
      confidence: number | null;
    }>;
  };
  language: string | null;
  status: 'processing' | 'completed' | 'failed';
  accuracy_score: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

async function getTranscript(videoId: string): Promise<Transcript> {
  const response = await fetch(`/api/videos/${videoId}/transcript`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Transcript not found');
    }
    throw new Error('Failed to fetch transcript');
  }

  return response.json();
}
```

---

### 2. Trigger Transcription

Start transcription for a video (async job).

**Endpoint:** `POST /videos/{video_id}/transcript/transcribe`

**Headers:**
```
Authorization: Bearer {token}
```

**Response (202 Accepted):**
```json
{
  "message": "Transcription job enqueued",
  "video_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Error Responses:**
- **404 Not Found:** Video doesn't exist
- **409 Conflict:** Transcription already in progress or completed
- **403 Forbidden:** User doesn't own the video

**UI Integration:**
```typescript
async function startTranscription(videoId: string): Promise<void> {
  const response = await fetch(`/api/videos/${videoId}/transcript/transcribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    if (response.status === 409) {
      throw new Error('Transcription already in progress');
    }
    throw new Error('Failed to start transcription');
  }

  // Start polling for progress
  pollTranscriptionProgress(videoId);
}
```

---

### 3. Get Transcription Progress

Poll for transcription progress (call every 2 seconds).

**Endpoint:** `GET /videos/{video_id}/transcript/progress`

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "video_id": "123e4567-e89b-12d3-a456-426614174001",
  "progress": 50,
  "status": "Transcribing audio...",
  "estimated_time_remaining": 120
}
```

**Progress Stages:**
- `0%` - "Not started"
- `10%` - "Downloading video..."
- `30%` - "Extracting audio..."
- `50%` - "Transcribing audio..."
- `90%` - "Saving transcript..."
- `100%` - "Complete"

**Error Status:**
- `status: "Failed: {error message}"` - Something went wrong

**UI Integration:**
```typescript
interface TranscriptionProgress {
  video_id: string;
  progress: number;
  status: string;
  estimated_time_remaining: number | null;
}

async function pollTranscriptionProgress(
  videoId: string,
  onProgress: (progress: TranscriptionProgress) => void
): Promise<void> {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/videos/${videoId}/transcript/progress`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data: TranscriptionProgress = await response.json();
      onProgress(data);

      // Stop polling when complete or failed
      if (data.progress === 100 || data.status.includes('Failed')) {
        clearInterval(interval);
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error);
      clearInterval(interval);
    }
  }, 2000); // Poll every 2 seconds
}
```

---

### 4. Export Transcript

Download transcript as SRT or VTT file.

**Endpoint:** `GET /videos/{video_id}/transcript/export?format={srt|vtt}`

**Query Parameters:**
- `format` (required): Either `srt` or `vtt`

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
- Content-Type: `text/srt` or `text/vtt`
- Content-Disposition: `attachment; filename="transcript_{video_id}.srt"`
- Body: File content

**Error Responses:**
- **400 Bad Request:** Invalid format
- **404 Not Found:** Video or transcript doesn't exist

**UI Integration:**
```typescript
function exportTranscript(videoId: string, format: 'srt' | 'vtt'): void {
  const url = `/api/videos/${videoId}/transcript/export?format=${format}`;

  // Trigger download
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('Authorization', `Bearer ${token}`);
  link.download = `transcript_${videoId}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

---

## Silence Removal API

### 1. Detect Silence Segments (Preview)

Preview silent segments without modifying the video.

**Endpoint:** `GET /videos/{video_id}/silence/segments`

**Query Parameters:**
- `threshold_db` (optional): Silence threshold in dB, range -60 to -20, default -40
- `min_duration_ms` (optional): Minimum silence duration in ms, range 500-5000, default 1000

**Headers:**
```
Authorization: Bearer {token}
```

**Example Request:**
```
GET /api/videos/{video_id}/silence/segments?threshold_db=-40&min_duration_ms=1000
```

**Response (200 OK):**
```json
{
  "segments": [
    {
      "start_time": 5.2,
      "end_time": 8.7,
      "duration": 3.5
    },
    {
      "start_time": 45.1,
      "end_time": 49.3,
      "duration": 4.2
    }
  ],
  "total_duration": 7.7,
  "original_duration": 120.0,
  "reduction_percentage": 6.4
}
```

**Field Descriptions:**
- `segments`: Array of detected silent segments
- `start_time`: Segment start in seconds
- `end_time`: Segment end in seconds
- `duration`: Segment duration in seconds
- `total_duration`: Total silence duration in seconds
- `original_duration`: Original video duration in seconds
- `reduction_percentage`: Percentage of video that would be removed

**UI Integration:**
```typescript
interface SilenceSegment {
  start_time: number;
  end_time: number;
  duration: number;
}

interface SilenceDetectionResponse {
  segments: SilenceSegment[];
  total_duration: number;
  original_duration: number;
  reduction_percentage: number;
}

async function detectSilence(
  videoId: string,
  thresholdDb: number = -40,
  minDurationMs: number = 1000
): Promise<SilenceDetectionResponse> {
  const url = `/api/videos/${videoId}/silence/segments?threshold_db=${thresholdDb}&min_duration_ms=${minDurationMs}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error('Failed to detect silence');
  }

  return response.json();
}
```

---

### 2. Remove Silence

Trigger silence removal job (async).

**Endpoint:** `POST /videos/{video_id}/silence/remove`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "threshold_db": -40,
  "min_duration_ms": 1000,
  "excluded_segments": [0, 2]
}
```

**Field Descriptions:**
- `threshold_db` (optional): Silence threshold in dB, default -40
- `min_duration_ms` (optional): Minimum silence duration in ms, default 1000
- `excluded_segments` (optional): Array of segment indices to NOT remove (e.g., [0, 2] keeps first and third segments)

**Response (202 Accepted):**
```json
{
  "message": "Silence removal job enqueued",
  "video_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Error Responses:**
- **422 Validation Error:** Invalid parameters (threshold out of range, etc.)
- **404 Not Found:** Video doesn't exist
- **403 Forbidden:** User doesn't own the video

**UI Integration:**
```typescript
interface SilenceRemovalRequest {
  threshold_db?: number;
  min_duration_ms?: number;
  excluded_segments?: number[];
}

async function removeSilence(
  videoId: string,
  options: SilenceRemovalRequest
): Promise<void> {
  const response = await fetch(`/api/videos/${videoId}/silence/remove`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(options)
  });

  if (!response.ok) {
    throw new Error('Failed to start silence removal');
  }

  // Start polling for progress
  pollSilenceRemovalProgress(videoId);
}
```

---

### 3. Get Silence Removal Progress

Poll for silence removal progress (call every 2 seconds).

**Endpoint:** `GET /videos/{video_id}/silence/progress`

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "video_id": "123e4567-e89b-12d3-a456-426614174001",
  "progress": 40,
  "status": "Removing segments...",
  "estimated_time_remaining": 60
}
```

**Progress Stages:**
- `0%` - "Not started"
- `10%` - "Downloading video..."
- `20%` - "Detecting silence..."
- `40%` - "Removing segments..."
- `80%` - "Uploading processed video..."
- `100%` - "Complete"

**UI Integration:**
```typescript
interface SilenceRemovalProgress {
  video_id: string;
  progress: number;
  status: string;
  estimated_time_remaining: number | null;
}

async function pollSilenceRemovalProgress(
  videoId: string,
  onProgress: (progress: SilenceRemovalProgress) => void
): Promise<void> {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/videos/${videoId}/silence/progress`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data: SilenceRemovalProgress = await response.json();
      onProgress(data);

      // Stop polling when complete or failed
      if (data.progress === 100 || data.status.includes('Failed')) {
        clearInterval(interval);
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error);
      clearInterval(interval);
    }
  }, 2000);
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning | When to Show |
|------|---------|--------------|
| 200 | OK | Success |
| 202 | Accepted | Job enqueued successfully |
| 400 | Bad Request | Invalid parameters - show validation error |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "Access denied" message |
| 404 | Not Found | Show "Resource not found" |
| 409 | Conflict | Show specific conflict message (e.g., "Already processing") |
| 422 | Validation Error | Show field-specific validation errors |
| 500 | Server Error | Show "Something went wrong, please try again" |

### Error Handling Example

```typescript
async function handleApiCall<T>(apiCall: () => Promise<Response>): Promise<T> {
  try {
    const response = await apiCall();

    if (!response.ok) {
      const error = await response.json();

      switch (response.status) {
        case 401:
          // Redirect to login
          window.location.href = '/login';
          throw new Error('Unauthorized');

        case 403:
          throw new Error('You do not have permission to perform this action');

        case 404:
          throw new Error('Resource not found');

        case 409:
          throw new Error(error.detail || 'Conflict occurred');

        case 422:
          throw new Error(error.detail || 'Invalid input');

        default:
          throw new Error(error.detail || 'An error occurred');
      }
    }

    return response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

---

## UI/UX Best Practices

### Transcription Flow

1. **Show "Start Transcription" Button**
   ```tsx
   <Button onClick={() => startTranscription(videoId)}>
     Generate Transcript
   </Button>
   ```

2. **Show Progress During Processing**
   ```tsx
   <ProgressBar value={progress} max={100} />
   <p>{status}</p>
   {estimatedTime && <p>About {estimatedTime}s remaining</p>}
   ```

3. **Display Transcript with Word Highlighting**
   ```tsx
   <TranscriptViewer
     transcript={transcript}
     currentTime={videoPlayer.currentTime}
     onWordClick={(timestamp) => videoPlayer.seek(timestamp)}
   />
   ```

4. **Offer Export Options**
   ```tsx
   <Button onClick={() => exportTranscript(videoId, 'srt')}>
     Download SRT
   </Button>
   <Button onClick={() => exportTranscript(videoId, 'vtt')}>
     Download VTT
   </Button>
   ```

---

### Silence Removal Flow

1. **Show "Preview Silence" Button**
   ```tsx
   <Button onClick={async () => {
     const detection = await detectSilence(videoId);
     setSegments(detection.segments);
   }}>
     Preview Silent Segments
   </Button>
   ```

2. **Display Timeline with Segment Markers**
   ```tsx
   <VideoTimeline duration={videoDuration}>
     {segments.map((seg, i) => (
       <SilenceMarker
         key={i}
         start={seg.start_time}
         end={seg.end_time}
         excluded={excludedSegments.includes(i)}
         onClick={() => toggleSegment(i)}
       />
     ))}
   </VideoTimeline>
   ```

3. **Show Estimated Time Savings**
   ```tsx
   <div>
     <p>Silent segments detected: {segments.length}</p>
     <p>Total silence: {formatDuration(totalDuration)}</p>
     <p>Video will be reduced by {reductionPercentage.toFixed(1)}%</p>
   </div>
   ```

4. **Confirm and Process**
   ```tsx
   <Button onClick={() => {
     removeSilence(videoId, {
       threshold_db: -40,
       min_duration_ms: 1000,
       excluded_segments: excludedSegments
     });
   }}>
     Remove Silence
   </Button>
   ```

5. **Show Progress**
   ```tsx
   <ProgressBar value={progress} max={100} />
   <p>{status}</p>
   ```

---

## Code Examples

### Complete Transcription Component

```tsx
import React, { useState, useEffect } from 'react';

interface TranscriptionPanelProps {
  videoId: string;
  token: string;
}

export function TranscriptionPanel({ videoId, token }: TranscriptionPanelProps) {
  const [transcript, setTranscript] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Check if transcript exists
  useEffect(() => {
    fetchTranscript();
  }, [videoId]);

  async function fetchTranscript() {
    try {
      const response = await fetch(`/api/videos/${videoId}/transcript`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTranscript(data);
      }
    } catch (error) {
      console.error('Failed to fetch transcript:', error);
    }
  }

  async function startTranscription() {
    setIsProcessing(true);

    try {
      await fetch(`/api/videos/${videoId}/transcript/transcribe`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Start polling
      pollProgress();
    } catch (error) {
      console.error('Failed to start transcription:', error);
      setIsProcessing(false);
    }
  }

  async function pollProgress() {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/videos/${videoId}/transcript/progress`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();
        setProgress(data.progress);
        setStatus(data.status);

        if (data.progress === 100) {
          clearInterval(interval);
          setIsProcessing(false);
          fetchTranscript();
        }
      } catch (error) {
        clearInterval(interval);
        setIsProcessing(false);
      }
    }, 2000);
  }

  function exportTranscript(format: 'srt' | 'vtt') {
    const url = `/api/videos/${videoId}/transcript/export?format=${format}`;
    window.open(url, '_blank');
  }

  if (!transcript && !isProcessing) {
    return (
      <button onClick={startTranscription}>
        Generate Transcript
      </button>
    );
  }

  if (isProcessing) {
    return (
      <div>
        <progress value={progress} max={100} />
        <p>{status}</p>
      </div>
    );
  }

  return (
    <div>
      <div>
        <button onClick={() => exportTranscript('srt')}>Export SRT</button>
        <button onClick={() => exportTranscript('vtt')}>Export VTT</button>
      </div>
      <div>
        <p>{transcript.full_text}</p>
      </div>
    </div>
  );
}
```

---

### Complete Silence Removal Component

```tsx
import React, { useState } from 'react';

interface SilenceRemovalPanelProps {
  videoId: string;
  token: string;
  videoDuration: number;
}

export function SilenceRemovalPanel({
  videoId,
  token,
  videoDuration
}: SilenceRemovalPanelProps) {
  const [segments, setSegments] = useState([]);
  const [excludedSegments, setExcludedSegments] = useState<number[]>([]);
  const [thresholdDb, setThresholdDb] = useState(-40);
  const [minDuration, setMinDuration] = useState(1000);
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  async function previewSilence() {
    try {
      const response = await fetch(
        `/api/videos/${videoId}/silence/segments?threshold_db=${thresholdDb}&min_duration_ms=${minDuration}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      const data = await response.json();
      setSegments(data.segments);
    } catch (error) {
      console.error('Failed to detect silence:', error);
    }
  }

  async function removeSilence() {
    setIsProcessing(true);

    try {
      await fetch(`/api/videos/${videoId}/silence/remove`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          threshold_db: thresholdDb,
          min_duration_ms: minDuration,
          excluded_segments: excludedSegments
        })
      });

      pollProgress();
    } catch (error) {
      console.error('Failed to remove silence:', error);
      setIsProcessing(false);
    }
  }

  async function pollProgress() {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/videos/${videoId}/silence/progress`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();
        setProgress(data.progress);

        if (data.progress === 100) {
          clearInterval(interval);
          setIsProcessing(false);
        }
      } catch (error) {
        clearInterval(interval);
        setIsProcessing(false);
      }
    }, 2000);
  }

  function toggleSegment(index: number) {
    setExcludedSegments(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  }

  if (isProcessing) {
    return (
      <div>
        <progress value={progress} max={100} />
        <p>Processing...</p>
      </div>
    );
  }

  return (
    <div>
      <div>
        <label>
          Threshold (dB):
          <input
            type="range"
            min={-60}
            max={-20}
            value={thresholdDb}
            onChange={(e) => setThresholdDb(Number(e.target.value))}
          />
          {thresholdDb}
        </label>

        <label>
          Min Duration (ms):
          <input
            type="range"
            min={500}
            max={5000}
            step={500}
            value={minDuration}
            onChange={(e) => setMinDuration(Number(e.target.value))}
          />
          {minDuration}
        </label>

        <button onClick={previewSilence}>Preview Silence</button>
      </div>

      {segments.length > 0 && (
        <div>
          <p>Found {segments.length} silent segments</p>
          <div>
            {segments.map((seg, i) => (
              <div
                key={i}
                onClick={() => toggleSegment(i)}
                style={{
                  opacity: excludedSegments.includes(i) ? 0.5 : 1,
                  cursor: 'pointer'
                }}
              >
                Segment {i + 1}: {seg.start_time.toFixed(1)}s - {seg.end_time.toFixed(1)}s
                ({seg.duration.toFixed(1)}s)
                {excludedSegments.includes(i) && ' [EXCLUDED]'}
              </div>
            ))}
          </div>

          <button onClick={removeSilence}>
            Remove Silence
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## Testing

### Testing with Postman/Curl

#### Get Transcript
```bash
curl -X GET "http://localhost:8000/api/videos/{VIDEO_ID}/transcript" \
  -H "Authorization: Bearer {TOKEN}"
```

#### Start Transcription
```bash
curl -X POST "http://localhost:8000/api/videos/{VIDEO_ID}/transcript/transcribe" \
  -H "Authorization: Bearer {TOKEN}"
```

#### Detect Silence
```bash
curl -X GET "http://localhost:8000/api/videos/{VIDEO_ID}/silence/segments?threshold_db=-40&min_duration_ms=1000" \
  -H "Authorization: Bearer {TOKEN}"
```

#### Remove Silence
```bash
curl -X POST "http://localhost:8000/api/videos/{VIDEO_ID}/silence/remove" \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_db": -40,
    "min_duration_ms": 1000,
    "excluded_segments": []
  }'
```

---

## Support

For questions or issues:
1. Check this documentation first
2. Review error messages in API responses
3. Check backend logs for detailed error information
4. Contact backend team for API-related issues

**Backend Team:** Agent 4 - Video Processing Specialist
**Documentation Version:** 1.0
**Last Updated:** 2025-11-09
