# Editor Components

This directory contains components for video editing features including silence removal and clip management.

## Components

### SilenceRemovalModal

Modal dialog for configuring and executing silence removal on videos.

**Features:**
- Adjustable threshold (dB) and minimum duration sliders
- Real-time preview of silence segments
- Before/after duration comparison
- Progress tracking during removal
- Visual segment list with timestamps

**Usage:**
```tsx
import { SilenceRemovalModal } from '@/components/editor'

<SilenceRemovalModal
  videoId={video.id}
  open={isOpen}
  onClose={() => setIsOpen(false)}
  onComplete={(outputVideoId) => {
    console.log('New video created:', outputVideoId)
  }}
/>
```

### KeywordSearchPanel

Search video transcripts for keywords and create clips from matches.

**Features:**
- Keyword search with context
- Match results with timestamps and excerpts
- Confidence scores for matches
- One-click clip creation from results
- Progress tracking for clip generation

**Usage:**
```tsx
import { KeywordSearchPanel } from '@/components/editor'

<KeywordSearchPanel
  videoId={video.id}
  onClipCreated={() => {
    // Refresh clips list
  }}
/>
```

### ClipsList

Display and manage all clips created from a video.

**Features:**
- Grid view with thumbnails
- Video preview on hover
- Download and delete actions
- Clip metadata (duration, timestamps, created date)
- Responsive layout

**Usage:**
```tsx
import { ClipsList } from '@/components/editor'

<ClipsList
  videoId={video.id}
  refreshTrigger={refreshCounter}
/>
```

### EditorToolbar

Integrated toolbar combining all editor features with tabbed interface.

**Features:**
- Tabbed interface for Clips and Search
- Silence removal button in header
- Automatic clip list refresh
- Clean, organized layout

**Usage:**
```tsx
import { EditorToolbar } from '@/components/editor'

<EditorToolbar video={video} />
```

## API Clients

### Silence API (`/lib/silence-api.ts`)

- `detectSilence(videoId, params)` - Detect silence segments
- `removeSilence(videoId, params)` - Remove silence and create new video
- `getSilenceProgress(videoId, jobId)` - Poll removal progress

### Clip API (`/lib/clip-api.ts`)

- `searchKeyword(videoId, keyword)` - Search transcript for keyword
- `createClip(videoId, data)` - Create clip from time range
- `getClips(videoId)` - Get all clips for video
- `getClip(clipId)` - Get single clip
- `deleteClip(clipId)` - Delete clip
- `getClipProgress(videoId, jobId)` - Poll clip generation progress

## Integration Example

Add the EditorToolbar to your video editor page:

```tsx
import { VideoEditor } from '@/components/timeline/VideoEditor'
import { EditorToolbar } from '@/components/editor'

export default function EditorPage({ video }) {
  return (
    <div className="flex flex-col h-screen">
      <VideoEditor video={video} />
      <EditorToolbar video={video} />
    </div>
  )
}
```

## Dependencies

- Radix UI components (Dialog, Slider, Tabs)
- Lucide React icons
- Shadcn UI components
- Tailwind CSS

## Notes

- All API calls include proper error handling with toast notifications
- Progress polling uses intervals with automatic cleanup
- Components are fully typed with TypeScript
- Responsive design with mobile support
