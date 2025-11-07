'use client'

import { useRouter } from 'next/navigation'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Play, Edit, Trash2 } from 'lucide-react'
import type { Video } from '@/types/video'
import { formatFileSize, formatDuration, formatRelativeTime } from '@/lib/utils'

interface VideoListProps {
  videos: Video[]
  onDelete?: (videoId: string) => void
  onEdit?: (videoId: string) => void
}

export function VideoList({ videos, onDelete, onEdit }: VideoListProps) {
  const router = useRouter()

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'processing':
        return 'secondary'
      case 'failed':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-muted-foreground">No videos found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Upload your first video to get started
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Thumbnail</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>File Size</TableHead>
            <TableHead>Upload Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {videos.map((video) => (
            <TableRow
              key={video.id}
              className="cursor-pointer"
              onClick={() => router.push(`/videos/${video.id}`)}
            >
              <TableCell>
                {video.thumbnail_url ? (
                  <div className="relative h-16 w-28 bg-muted rounded overflow-hidden">
                    <img
                      src={video.thumbnail_url}
                      alt={video.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="relative h-16 w-28 bg-muted flex items-center justify-center rounded">
                    <Play className="h-6 w-6 text-muted-foreground" />
                  </div>
                )}
              </TableCell>
              <TableCell className="font-medium">{video.title}</TableCell>
              <TableCell>
                {video.duration ? formatDuration(video.duration) : '-'}
              </TableCell>
              <TableCell>
                {video.file_size ? formatFileSize(video.file_size) : '-'}
              </TableCell>
              <TableCell>{formatRelativeTime(video.created_at)}</TableCell>
              <TableCell>
                <Badge variant={getStatusBadgeVariant(video.status)}>
                  {video.status}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (onEdit) onEdit(video.id)
                    }}
                    title="Edit"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (onDelete) onDelete(video.id)
                    }}
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

