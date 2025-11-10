"use client";

import { memo } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Edit, Trash2 } from "lucide-react";
import type { Video } from "@/types/video";
import {
  formatFileSize,
  formatDuration,
  formatRelativeTime,
} from "@/lib/utils";

interface VideoCardProps {
  video: Video;
  onDelete?: (videoId: string) => void;
  onEdit?: (videoId: string) => void;
}

export const VideoCard = memo(
  function VideoCard({ video, onDelete, onEdit }: VideoCardProps) {
    const router = useRouter();

    const getStatusBadgeVariant = (status: string) => {
      switch (status) {
        case "completed":
          return "default";
        case "processing":
          return "secondary";
        case "failed":
          return "destructive";
        default:
          return "outline";
      }
    };

    const handleCardClick = () => {
      router.push(`/videos/${video.id}`);
    };

    const handleDelete = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onDelete) {
        onDelete(video.id);
      }
    };

    const handleEdit = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onEdit) {
        onEdit(video.id);
      }
    };

    return (
      <Card
        className="cursor-pointer transition-shadow hover:shadow-lg"
        onClick={handleCardClick}
      >
        <CardHeader className="p-0">
          {/* Thumbnail or placeholder */}
          {video.thumbnail_url ? (
            <div className="relative aspect-video w-full overflow-hidden">
              <img
                src={video.thumbnail_url}
                alt={video.title}
                className="w-full h-full object-cover"
              />
              {video.status === "processing" && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <Badge variant="secondary">Processing</Badge>
                </div>
              )}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity bg-black/30">
                <Play className="h-12 w-12 text-white" />
              </div>
            </div>
          ) : (
            <div className="relative aspect-video w-full bg-muted flex items-center justify-center">
              <Play className="h-12 w-12 text-muted-foreground" />
              {video.status === "processing" && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <Badge variant="secondary">Processing</Badge>
                </div>
              )}
            </div>
          )}
        </CardHeader>
        <CardContent className="p-4">
          <h3 className="font-semibold text-lg mb-2 line-clamp-2">
            {video.title}
          </h3>
          <div className="space-y-1 text-sm text-muted-foreground">
            {video.duration && (
              <div>Duration: {formatDuration(video.duration)}</div>
            )}
            {video.file_size && (
              <div>Size: {formatFileSize(video.file_size)}</div>
            )}
            <div>Uploaded: {formatRelativeTime(video.created_at)}</div>
          </div>
        </CardContent>
        <CardFooter className="p-4 pt-0 flex items-center justify-between">
          <Badge variant={getStatusBadgeVariant(video.status)}>
            {video.status}
          </Badge>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleEdit}
              title="Edit"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardFooter>
      </Card>
    );
  },
  (prev, next) => {
    // Custom comparison: only re-render if video data or callbacks change
    return (
      prev.video.id === next.video.id &&
      prev.video.title === next.video.title &&
      prev.video.status === next.video.status &&
      prev.video.thumbnail_url === next.video.thumbnail_url &&
      prev.onDelete === next.onDelete &&
      prev.onEdit === next.onEdit
    );
  },
);
