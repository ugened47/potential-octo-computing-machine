"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useToast } from "@/components/ui/use-toast";
import {
  detectSilence,
  removeSilence,
  getSilenceProgress,
  type SilenceSegment,
} from "@/lib/silence-api";
import {
  formatTime,
  formatDuration,
  calculateTotalDuration,
} from "@/lib/utils";
import { Volume2, VolumeX } from "lucide-react";

interface SilenceRemovalModalProps {
  videoId: string;
  open: boolean;
  onClose: () => void;
  onComplete?: (outputVideoId: string) => void;
}

export function SilenceRemovalModal({
  videoId,
  open,
  onClose,
  onComplete,
}: SilenceRemovalModalProps) {
  const { toast } = useToast();

  // Settings
  const [threshold, setThreshold] = useState([-40]);
  const [minDuration, setMinDuration] = useState([1.0]);

  // State
  const [segments, setSegments] = useState<SilenceSegment[]>([]);
  const [loading, setLoading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [totalDuration, setTotalDuration] = useState(0);

  // Load segments when settings change
  useEffect(() => {
    if (open && videoId) {
      loadSegments();
    }
  }, [threshold[0], minDuration[0], open, videoId]);

  // Poll progress when removing
  useEffect(() => {
    if (!removing || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const status = await getSilenceProgress(videoId, jobId);
        setProgress(status.progress);

        if (status.status === "completed") {
          clearInterval(interval);
          setRemoving(false);
          toast({
            title: "Success",
            description: "Silence removed successfully",
          });
          if (onComplete && status.output_video_id) {
            onComplete(status.output_video_id);
          }
          onClose();
        } else if (status.status === "failed") {
          clearInterval(interval);
          setRemoving(false);
          toast({
            title: "Error",
            description: status.message || "Failed to remove silence",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Failed to get progress:", error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [removing, jobId, videoId, onComplete, onClose, toast]);

  const loadSegments = async () => {
    setLoading(true);
    try {
      const data = await detectSilence(videoId, {
        threshold_db: threshold[0],
        min_duration: minDuration[0],
      });
      setSegments(data.segments);
      setTotalDuration(data.total_duration);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to detect silence",
        variant: "destructive",
      });
      console.error("Failed to detect silence:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    setProgress(0);

    try {
      const result = await removeSilence(videoId, {
        threshold_db: threshold[0],
        min_duration: minDuration[0],
      });
      setJobId(result.job_id);
    } catch (error) {
      setRemoving(false);
      toast({
        title: "Error",
        description: "Failed to start silence removal",
        variant: "destructive",
      });
      console.error("Failed to remove silence:", error);
    }
  };

  const totalSilenceDuration = calculateTotalDuration(segments);
  const estimatedOutputDuration = totalDuration - totalSilenceDuration;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Remove Silence</DialogTitle>
          <DialogDescription>
            Configure silence detection settings and preview segments to be
            removed
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Threshold Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Threshold (dB)</label>
              <Badge variant="secondary">{threshold[0]} dB</Badge>
            </div>
            <Slider
              value={threshold}
              onValueChange={setThreshold}
              min={-60}
              max={-20}
              step={1}
              disabled={removing}
            />
            <p className="text-xs text-muted-foreground">
              Audio below this volume level will be considered silence
            </p>
          </div>

          {/* Minimum Duration Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">
                Minimum Duration (seconds)
              </label>
              <Badge variant="secondary">{minDuration[0].toFixed(1)}s</Badge>
            </div>
            <Slider
              value={minDuration}
              onValueChange={setMinDuration}
              min={0.5}
              max={5.0}
              step={0.5}
              disabled={removing}
            />
            <p className="text-xs text-muted-foreground">
              Only silence lasting longer than this will be removed
            </p>
          </div>

          {/* Preview Section */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold flex items-center gap-2">
                <VolumeX className="h-4 w-4" />
                Silence Segments Preview
              </h3>
              {loading && <LoadingSpinner />}
            </div>

            {loading ? (
              <p className="text-sm text-muted-foreground">
                Detecting silence...
              </p>
            ) : (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Segments</p>
                    <p className="font-semibold">{segments.length}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Total Silence</p>
                    <p className="font-semibold">
                      {formatDuration(totalSilenceDuration)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-muted-foreground">New Duration</p>
                    <p className="font-semibold text-green-600">
                      {formatDuration(estimatedOutputDuration)}
                    </p>
                  </div>
                </div>

                {/* Segments List */}
                {segments.length > 0 ? (
                  <div className="max-h-48 overflow-y-auto space-y-2">
                    {segments.map((seg, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-sm p-2 bg-secondary/50 rounded"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">
                            #{idx + 1}
                          </span>
                          <span className="font-mono">
                            {formatTime(seg.start)} - {formatTime(seg.end)}
                          </span>
                        </div>
                        <Badge variant="outline">
                          {formatDuration(seg.duration)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Volume2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No silence detected with current settings</p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Progress Section */}
          {removing && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Removing silence...</span>
                <span className="text-muted-foreground">{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={onClose} variant="outline" disabled={removing}>
            Cancel
          </Button>
          <Button
            onClick={handleRemove}
            disabled={loading || removing || segments.length === 0}
          >
            {removing
              ? "Removing..."
              : `Remove ${segments.length} Segment${segments.length !== 1 ? "s" : ""}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
