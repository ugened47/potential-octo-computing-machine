"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RefreshCw, ExternalLink } from "lucide-react";
import { getVideos } from "@/lib/video-api";
import type { Video } from "@/types/video";
import { formatRelativeTime } from "@/lib/utils";

interface ProcessingQueueProps {
  pollInterval?: number;
}

export function ProcessingQueue({ pollInterval = 5000 }: ProcessingQueueProps) {
  const router = useRouter();
  const [processingVideos, setProcessingVideos] = useState<Video[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProcessingVideos = async () => {
    try {
      const videos = await getVideos({ status: "processing" });
      setProcessingVideos(videos);
    } catch (error) {
      console.error("Failed to fetch processing videos:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchProcessingVideos();

    // Set up polling
    const intervalId = setInterval(fetchProcessingVideos, pollInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [pollInterval]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Processing Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (processingVideos.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Processing Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            No videos are currently being processed
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Processing Queue</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchProcessingVideos}
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {processingVideos.map((video) => (
            <div
              key={video.id}
              className="flex items-center justify-between rounded-lg border p-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="font-medium">{video.title}</h4>
                  <Badge variant="secondary">Processing</Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  Uploaded {formatRelativeTime(video.created_at)}
                </div>
                <Progress value={50} className="mt-2" />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push(`/videos/${video.id}`)}
                className="ml-4"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
