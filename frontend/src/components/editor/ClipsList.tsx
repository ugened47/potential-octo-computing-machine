"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/use-toast";
import { getClips, deleteClip, type Clip } from "@/lib/clip-api";
import { formatTime, formatDuration } from "@/lib/utils";
import { Trash2, Download, Play, Film } from "lucide-react";

interface ClipsListProps {
  videoId: string;
  refreshTrigger?: number;
}

export function ClipsList({ videoId, refreshTrigger }: ClipsListProps) {
  const { toast } = useToast();

  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadClips();
  }, [videoId, refreshTrigger]);

  const loadClips = async () => {
    setLoading(true);
    try {
      const data = await getClips(videoId);
      setClips(data.clips);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load clips",
        variant: "destructive",
      });
      console.error("Failed to load clips:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (clipId: string) => {
    if (!confirm("Are you sure you want to delete this clip?")) {
      return;
    }

    setDeleting(clipId);
    try {
      await deleteClip(clipId);
      setClips((prev) => prev.filter((clip) => clip.id !== clipId));
      toast({
        title: "Success",
        description: "Clip deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete clip",
        variant: "destructive",
      });
      console.error("Failed to delete clip:", error);
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = (clip: Clip) => {
    // Open clip URL in new tab for download
    window.open(clip.url, "_blank");
  };

  const handlePlayClip = (clip: Clip) => {
    // Open clip in new tab for playback
    window.open(clip.url, "_blank");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
        <span className="ml-2 text-sm text-muted-foreground">
          Loading clips...
        </span>
      </div>
    );
  }

  if (clips.length === 0) {
    return (
      <EmptyState
        icon={Film}
        title="No clips yet"
        description="Search for keywords and create clips to get started"
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Film className="h-4 w-4" />
          Generated Clips ({clips.length})
        </h3>
        <Button variant="outline" size="sm" onClick={loadClips}>
          Refresh
        </Button>
      </div>

      {/* Clips Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {clips.map((clip) => (
          <Card
            key={clip.id}
            className="overflow-hidden hover:shadow-md transition-shadow"
          >
            <CardContent className="p-0">
              {/* Thumbnail/Video Preview */}
              <div className="relative aspect-video bg-muted group">
                {clip.thumbnail_url ? (
                  <img
                    src={clip.thumbnail_url}
                    alt={clip.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center w-full h-full">
                    <Film className="h-12 w-12 text-muted-foreground opacity-50" />
                  </div>
                )}

                {/* Play Overlay */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                  <Button
                    size="icon"
                    variant="secondary"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => handlePlayClip(clip)}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                </div>

                {/* Duration Badge */}
                <Badge
                  variant="secondary"
                  className="absolute bottom-2 right-2 font-mono text-xs"
                >
                  {formatDuration(clip.duration)}
                </Badge>
              </div>

              {/* Clip Info */}
              <div className="p-3 space-y-2">
                <div>
                  <h4 className="font-medium text-sm line-clamp-1">
                    {clip.title}
                  </h4>
                  <p className="text-xs text-muted-foreground font-mono">
                    {formatTime(clip.start)} - {formatTime(clip.end)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-8"
                    onClick={() => handleDownload(clip)}
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Download
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 px-2"
                    onClick={() => handleDelete(clip.id)}
                    disabled={deleting === clip.id}
                  >
                    {deleting === clip.id ? (
                      <LoadingSpinner />
                    ) : (
                      <Trash2 className="h-3 w-3 text-destructive" />
                    )}
                  </Button>
                </div>

                {/* Created Date */}
                <p className="text-xs text-muted-foreground">
                  Created {new Date(clip.created_at).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
