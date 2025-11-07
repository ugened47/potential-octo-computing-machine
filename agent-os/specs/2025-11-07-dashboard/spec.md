# Specification: Dashboard

## Goal
Provide a central dashboard for users to view all uploaded videos, track processing status, access quick actions, and view usage statistics.

## User Stories
- As a content creator, I want to see all my videos in one place so that I can easily manage my content
- As a user, I want to see processing status so that I know when my videos are ready to edit

## Specific Requirements

**Dashboard API**
- GET /api/dashboard/stats: Return user statistics (total videos, total clips, total processing time, storage used)
- GET /api/videos: List user's videos with filtering (status, date range) and sorting (date, name, duration)
- GET /api/videos?status=processing: Filter videos by processing status
- GET /api/videos?sort=created_at&order=desc: Sort videos by creation date descending
- Support pagination with limit and offset parameters

**Dashboard Page Layout**
- Stats cards section at top showing key metrics
- Recent videos section showing latest uploads
- Processing queue section showing videos currently processing
- Video grid/list view toggle
- Search bar for finding videos by title
- Upload button prominently displayed

**Stats Cards**
- Total Videos: Count of all user's videos
- Storage Used: Total size of all videos (GB)
- Processing Time: Total minutes of video processed
- Recent Activity: Count of videos uploaded in last 7 days
- Display cards in responsive grid (4 columns desktop, 2 mobile)

**Video Grid/List View**
- Grid view: Card layout with video thumbnails (placeholder initially)
- List view: Table layout with columns (thumbnail, title, duration, date, status, actions)
- Toggle between grid and list views with button
- Responsive: Grid on desktop, list on mobile
- Empty state message when no videos uploaded

**Video Cards**
- Display video thumbnail (placeholder image initially)
- Show video title (truncate if long)
- Display metadata: duration, file size, upload date
- Show processing status badge (uploaded, processing, completed, failed)
- Action buttons: View, Edit, Delete (on hover or menu)
- Click card to navigate to video detail/edit page

**Video List Table**
- Columns: Thumbnail, Title, Duration, File Size, Upload Date, Status, Actions
- Sortable columns (click header to sort)
- Status column with colored badges
- Actions column with dropdown menu (View, Edit, Delete, Download)
- Responsive: Hide some columns on mobile

**Quick Actions**
- View button: Navigate to video editor/viewer page
- Edit button: Navigate to video editor with timeline
- Delete button: Show confirmation dialog, then delete video and S3 file
- Duplicate button: Create copy of video (post-MVP, out of scope)
- Download button: Download original video file

**Processing Queue**
- Section showing videos with status: processing, queued
- Display processing progress for each video
- Show estimated time remaining
- Auto-refresh every 5 seconds to update status
- Link to view video details

**Filtering & Sorting**
- Filter by status: All, Uploaded, Processing, Completed, Failed
- Sort by: Date (newest/oldest), Name (A-Z/Z-A), Duration (longest/shortest)
- Search by title: Real-time search as user types
- Clear filters button to reset all filters

**Recent Videos**
- Show last 5-10 videos uploaded
- Display in compact card format
- Show upload time relative (e.g., "2 hours ago")
- Click to navigate to video

**Empty States**
- No videos: "Upload your first video" message with upload button
- No processing: Hide processing queue section
- No search results: "No videos found" message with clear search button

**Navigation Integration**
- Dashboard as home page (/dashboard)
- Sidebar navigation (if implemented) highlighting Dashboard
- Breadcrumbs showing current page
- Back button to return to previous page

**Frontend Component Specifications**

**DashboardPage Component (Server/Client Hybrid)**
- Server Component: Fetches initial data (stats, videos) on server
- Client Component: Interactive elements (search, filters, view toggle)
- Props: initialStats (DashboardStats), initialVideos (Video[])
- Features: Stats cards, video grid/list, processing queue, search bar, upload button
- Layout: Responsive grid layout, sidebar (if implemented), main content area

**StatsCards Component (Client Component)**
- Props: stats (DashboardStats)
- Features: Four stat cards (Total Videos, Storage Used, Processing Time, Recent Activity)
- Rendering: Responsive grid (4 columns desktop, 2 mobile), card layout with icons
- Shadcn/ui: Card component, icons from lucide-react
- Formatting: Number formatting, size formatting (GB), time formatting

**VideoGrid Component (Client Component)**
- Props: videos (Video[]), onVideoClick (function), onVideoDelete (function)
- State: selectedVideos (Set<string>)
- Features: Grid layout with video cards, hover effects, action buttons
- Rendering: Responsive grid, placeholder thumbnails, metadata display
- Actions: View, Edit, Delete buttons on hover or menu

**VideoList Component (Client Component)**
- Props: videos (Video[]), sortBy (string), sortOrder ('asc' | 'desc'), onVideoClick (function)
- Features: Table layout, sortable columns, status badges, action dropdown
- Rendering: Shadcn/ui Table component, responsive (hides columns on mobile)
- Sorting: Click column header to sort, visual indicator for sort direction

**VideoCard Component (Client Component)**
- Props: video (Video), onClick (function), onDelete (function), onEdit (function)
- Features: Thumbnail (placeholder), title, metadata, status badge, action menu
- Rendering: Card layout, hover effects, action buttons on hover
- Shadcn/ui: Card, Badge, Button, DropdownMenu components

**ProcessingQueue Component (Client Component)**
- Props: videos (Video[]), onVideoClick (function)
- State: isPolling (boolean)
- Features: Auto-refresh every 5 seconds, progress indicators, estimated time
- Rendering: List of processing videos, progress bars, status badges
- API: Polls getVideos with status=processing filter

**VideoSearch Component (Client Component)**
- Props: onSearchChange (function), placeholder (string, optional)
- State: searchQuery (string)
- Features: Real-time search, clear button, debounced input (300ms)
- Rendering: Input component with Search icon, similar to TranscriptSearch pattern

**VideoFilters Component (Client Component)**
- Props: onFilterChange (function), onSortChange (function), currentFilters (FilterState)
- State: statusFilter (string), sortBy (string), sortOrder ('asc' | 'desc')
- Features: Status dropdown, sort dropdown, clear filters button
- Shadcn/ui: Select component for dropdowns, Button for clear

**Frontend API Client Functions (TypeScript)**
- getDashboardStats(): Promise<DashboardStats>
- getVideos(filters?: VideoFilters, pagination?: Pagination): Promise<Video[]>
- getVideo(videoId: string): Promise<Video>
- deleteVideo(videoId: string): Promise<void>
- All functions use apiClient with error handling

**TypeScript Type Definitions**
- DashboardStats: { total_videos: number, total_clips: number, total_processing_time: number, storage_used: number, recent_activity: number }
- VideoFilters: { status?: VideoStatus, date_from?: string, date_to?: string, search?: string }
- Pagination: { limit: number, offset: number }
- Video: { id: string, title: string, duration: number, file_size: number, status: VideoStatus, created_at: string, ... }
- Types defined in frontend/src/types/dashboard.ts and frontend/src/types/video.ts

**State Management**
- Dashboard state: Server Component for initial data, Client Component for interactions
- Filter/sort state: URL query parameters for shareable state
- View preference: LocalStorage or Zustand for grid/list preference
- Processing queue: Polling state managed in ProcessingQueue component

**Empty States**
- No videos: Shows "Upload your first video" message with upload button
- No processing: Hides processing queue section
- No search results: Shows "No videos found" with clear search button
- Shadcn/ui: Empty state components with icons and actions

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for cards, tables, buttons, and badges.

## Existing Code to Leverage

**Video Model**
- Reference Video model from video-upload spec
- Use video metadata fields for display
- Follow same video access patterns

**API Route Structure**
- Follow FastAPI router pattern from existing routes
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation
- Follow pagination patterns from other list endpoints

**Frontend Components**
- Use Shadcn/ui Card component for video cards
- Use Shadcn/ui Table component for list view
- Use Shadcn/ui Badge component for status indicators
- Use Shadcn/ui Button component for actions
- Use Shadcn/ui Input component for search

**State Management**
- Use Zustand or React state for view preferences (grid/list)
- Store filter and sort state in URL query parameters
- Follow project's state management patterns

**Next.js Patterns**
- Use Server Components for initial data fetching
- Use Client Components for interactive elements (toggle, search)
- Follow App Router patterns from project structure
- Use Next.js Link for navigation

**Authentication**
- Reference authentication patterns for protected routes
- Use same user context/state management
- Follow same redirect patterns for unauthenticated users

**Video Actions**
- Reference video deletion patterns from video-upload spec
- Follow same confirmation dialog patterns
- Use same error handling for failed operations

## Out of Scope
- Video sharing or collaboration features (single user only)
- Video organization with folders or tags (flat list only)
- Bulk operations (select multiple videos for batch actions)
- Video analytics or view statistics (post-MVP feature)
- Custom dashboard widgets or layout customization
- Video playlists or collections (post-MVP feature)
- Export dashboard data (CSV, etc.)
- Advanced filtering (date range picker, file size range)
- Video comparison or side-by-side view
- Dashboard customization or personalization settings

