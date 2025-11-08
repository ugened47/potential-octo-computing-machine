"use client";

import { useState, useEffect } from "react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, X, Upload, CheckCircle2 } from "lucide-react";

export type UploadStatus =
  | "preparing"
  | "uploading"
  | "processing"
  | "complete"
  | "error";

interface UploadProgressProps {
  progress: number; // 0-100
  status: UploadStatus;
  uploadSpeed?: number; // MB/s
  estimatedTimeRemaining?: number; // seconds
  error?: string | null;
  onRetry?: () => void;
  onCancel?: () => void;
}

export function UploadProgress({
  progress,
  status,
  uploadSpeed,
  estimatedTimeRemaining,
  error,
  onRetry,
  onCancel,
}: UploadProgressProps) {
  const getStatusIcon = () => {
    switch (status) {
      case "complete":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      case "uploading":
        return <Upload className="h-4 w-4 animate-pulse" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "preparing":
        return "Preparing upload...";
      case "uploading":
        return "Uploading...";
      case "processing":
        return "Processing...";
      case "complete":
        return "Upload complete!";
      case "error":
        return "Upload failed";
      default:
        return "Unknown status";
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${Math.ceil(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.ceil(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="space-y-4 p-4">
      {/* Status and progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium">{getStatusText()}</span>
          </div>
          <span className="text-muted-foreground">{progress}%</span>
        </div>
        <Progress value={progress} />
      </div>

      {/* Upload speed and time remaining */}
      {(status === "uploading" || status === "processing") && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          {uploadSpeed && <span>Speed: {uploadSpeed.toFixed(2)} MB/s</span>}
          {estimatedTimeRemaining && (
            <span>Time remaining: {formatTime(estimatedTimeRemaining)}</span>
          )}
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {status === "error" && onRetry && (
          <Button onClick={onRetry} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Upload
          </Button>
        )}
        {(status === "preparing" || status === "uploading") && onCancel && (
          <Button onClick={onCancel} variant="outline" size="sm">
            <X className="mr-2 h-4 w-4" />
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}
