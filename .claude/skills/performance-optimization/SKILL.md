---
name: performance-optimization
description: Analyze and optimize application performance for both backend (Python/FastAPI) and frontend (Next.js/React). Use when investigating slow endpoints, optimizing database queries, or improving frontend render performance.
allowed-tools: Read, Grep, Glob
---

# Performance Optimization Specialist

You are a performance expert for the AI Video Editor project.

## Expertise Areas

- **Backend Performance**: Async operations, database optimization, caching
- **Frontend Performance**: React rendering, bundle size, lazy loading
- **Video Processing**: Stream processing, memory management, parallelization
- **Database**: Query optimization, indexing, connection pooling
- **Caching**: Redis strategies, CDN usage

## Backend Optimization

### Async/Await Patterns

**ALWAYS use async**:
```python
# GOOD: Async database operations
async def get_user_videos(user_id: UUID, session: AsyncSession):
    result = await session.execute(
        select(Video).where(Video.user_id == user_id)
    )
    return result.scalars().all()

# BAD: Blocking operations
def get_user_videos(user_id: UUID, session: Session):
    return session.query(Video).filter_by(user_id=user_id).all()
```

**Parallel async operations**:
```python
import asyncio

# Run independent operations in parallel
user_task = session.get(User, user_id)
videos_task = session.execute(select(Video).where(Video.user_id == user_id))
stats_task = get_user_stats(user_id)

user, videos_result, stats = await asyncio.gather(
    user_task,
    videos_task,
    stats_task
)
videos = videos_result.scalars().all()
```

### Database Optimization

**Avoid N+1 queries**:
```python
# BAD: N+1 query problem
videos = await session.execute(select(Video))
for video in videos.scalars():
    clips = await session.execute(
        select(Clip).where(Clip.video_id == video.id)
    )  # N additional queries!

# GOOD: Eager loading
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(Video).options(selectinload(Video.clips))
)
videos = result.scalars().all()
# Now video.clips is already loaded
```

**Use indexes**:
```python
# Add index in migration
def upgrade():
    op.create_index(
        'idx_videos_user_id_created_at',
        'videos',
        ['user_id', 'created_at'],
    )

    # Partial index for specific queries
    op.execute("""
        CREATE INDEX idx_videos_processing
        ON videos (user_id, created_at)
        WHERE status = 'processing'
    """)
```

**Pagination**:
```python
@router.get("/videos")
async def list_videos(
    skip: int = 0,
    limit: int = Query(20, le=100),  # Max 100 per request
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(Video)
        .offset(skip)
        .limit(limit)
        .order_by(Video.created_at.desc())
    )
    return result.scalars().all()
```

### Caching Strategy

**Redis caching**:
```python
from redis import Redis
import json

async def get_user_stats(user_id: UUID, redis: Redis):
    # Try cache first
    cache_key = f"user_stats:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Calculate stats
    stats = await calculate_stats(user_id)

    # Cache for 5 minutes
    await redis.setex(
        cache_key,
        300,  # TTL in seconds
        json.dumps(stats)
    )

    return stats
```

**Invalidate cache on updates**:
```python
@router.post("/videos")
async def create_video(
    video: VideoCreate,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    # Create video...

    # Invalidate user stats cache
    await redis.delete(f"user_stats:{current_user.id}")

    return created_video
```

### Connection Pooling

**Database pool**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Max connections
    max_overflow=10,       # Additional connections when pool is full
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

## Frontend Optimization

### Bundle Size

**Analyze bundle**:
```bash
cd frontend && npm run build
# Check .next/analyze output
```

**Code splitting**:
```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic'

const VideoEditor = dynamic(
  () => import('@/components/editor/video-editor'),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[600px]" />
  }
)

// Lazy load third-party libraries
const Wavesurfer = dynamic(
  () => import('wavesurfer.js').then(mod => mod.default),
  { ssr: false }
)
```

### React Performance

**Avoid unnecessary re-renders**:
```typescript
import { memo, useMemo, useCallback } from 'react'

// Memo component
export const VideoCard = memo(({ video, onDelete }: VideoCardProps) => {
  return <Card>...</Card>
}, (prev, next) => {
  // Custom comparison
  return prev.video.id === next.video.id
})

// Memo expensive computations
const sortedVideos = useMemo(
  () => videos.sort((a, b) => b.createdAt - a.createdAt),
  [videos]
)

// Memo callbacks
const handleDelete = useCallback(
  (id: string) => {
    deleteVideo(id)
  },
  [deleteVideo]
)
```

**Virtualize long lists**:
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

// Only render visible items
const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 100,
  overscan: 5  // Render 5 items above/below viewport
})
```

**Debounce expensive operations**:
```typescript
import { useDebouncedCallback } from 'use-debounce'

const handleSearch = useDebouncedCallback(
  async (query: string) => {
    const results = await searchVideos(query)
    setResults(results)
  },
  300  // Wait 300ms after user stops typing
)
```

### Image Optimization

**Use Next.js Image**:
```typescript
import Image from 'next/image'

<Image
  src={video.thumbnailUrl}
  alt={video.title}
  width={320}
  height={180}
  placeholder="blur"
  blurDataURL={video.blurHash}
  loading="lazy"
/>
```

### API Optimization

**Request deduplication**:
```typescript
import { useQuery } from '@tanstack/react-query'

// React Query automatically deduplicates requests
const { data } = useQuery({
  queryKey: ['video', videoId],
  queryFn: () => fetchVideo(videoId),
  staleTime: 60000,  // Consider data fresh for 1 minute
})
```

**Prefetch data**:
```typescript
// Prefetch on hover
<Link
  href={`/videos/${video.id}`}
  onMouseEnter={() => {
    queryClient.prefetchQuery({
      queryKey: ['video', video.id],
      queryFn: () => fetchVideo(video.id),
    })
  }}
>
  View Video
</Link>
```

## Video Processing Performance

### Stream Processing

**Avoid loading entire video**:
```python
import av

# GOOD: Stream processing
async def extract_audio(input_path: str, output_path: str):
    container = av.open(input_path)
    output = av.open(output_path, 'w')

    audio_stream = output.add_stream('aac')

    for packet in container.demux(audio=0):
        for frame in packet.decode():
            # Process frame by frame
            for packet in audio_stream.encode(frame):
                output.mux(packet)

    # Flush
    for packet in audio_stream.encode():
        output.mux(packet)

    output.close()
    container.close()

# BAD: Loading entire video
video_bytes = open(input_path, 'rb').read()  # Don't do this!
```

### Parallel Processing

**Use multiprocessing for CPU-bound tasks**:
```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

async def process_multiple_videos(video_ids: List[UUID]):
    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, process_video, video_id)
            for video_id in video_ids
        ]
        results = await asyncio.gather(*tasks)

    return results
```

## Monitoring

**Log slow queries**:
```python
import time
from functools import wraps

def log_slow_queries(threshold: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start

            if duration > threshold:
                logger.warning(
                    f"Slow query: {func.__name__} took {duration:.2f}s"
                )

            return result
        return wrapper
    return decorator
```

**Profile endpoints**:
```python
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions
```

## Performance Checklist

**Backend**:
- ✓ All I/O operations are async
- ✓ Database queries use indexes
- ✓ N+1 queries eliminated with eager loading
- ✓ Pagination on list endpoints
- ✓ Caching for expensive computations
- ✓ Background jobs for long-running tasks
- ✓ Connection pooling configured

**Frontend**:
- ✓ Code splitting for large components
- ✓ Components memoized where appropriate
- ✓ Long lists virtualized
- ✓ Images optimized with Next.js Image
- ✓ User input debounced
- ✓ Bundle size < 200KB (gzipped)
- ✓ Lighthouse score > 90

Focus on measuring first, then optimizing the biggest bottlenecks.
