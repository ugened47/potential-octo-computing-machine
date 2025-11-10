"use client";

import { memo } from "react";
import { VideoCard } from "./VideoCard";
import type { Video } from "@/types/video";

interface VideoGridProps {
  videos: Video[];
  onDelete?: (videoId: string) => void;
  onEdit?: (videoId: string) => void;
}

export const VideoGrid = memo(function VideoGrid({
  videos,
  onDelete,
  onEdit,
}: VideoGridProps) {
  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-muted-foreground">No videos found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Upload your first video to get started
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onDelete={onDelete}
          onEdit={onEdit}
        />
      ))}
    </div>
  );
});
