"use client";

import { useState, useEffect } from "react";
import { TranscriptDisplay } from "./TranscriptDisplay";
import { TranscriptSearch } from "./TranscriptSearch";
import { TranscriptionProgress } from "./TranscriptionProgress";
import { TranscriptExport } from "./TranscriptExport";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { Transcript, TranscriptStatus } from "@/types/transcript";
import { getTranscript } from "@/lib/transcript-api";

interface TranscriptPanelProps {
  videoId: string;
  currentTime?: number;
  onSeek?: (timestamp: number) => void;
}

export function TranscriptPanel({
  videoId,
  currentTime = 0,
  onSeek,
}: TranscriptPanelProps) {
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<TranscriptStatus>("processing");

  useEffect(() => {
    const fetchTranscript = async () => {
      try {
        setIsLoading(true);
        const data = await getTranscript(videoId);
        setTranscript(data);
        setStatus(data.status);
        setError(null);
      } catch (err) {
        if (err instanceof Error && err.message.includes("404")) {
          // Transcript not found - might be processing
          setStatus("processing");
        } else {
          setError(
            err instanceof Error ? err.message : "Failed to load transcript",
          );
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchTranscript();
  }, [videoId]);

  const handleTranscriptComplete = () => {
    // Refetch transcript when transcription completes
    const refetch = async () => {
      try {
        const data = await getTranscript(videoId);
        setTranscript(data);
        setStatus(data.status);
      } catch (err) {
        console.error("Failed to refetch transcript:", err);
      }
    };
    refetch();
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error && status !== "processing") {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <div className="text-sm text-destructive">{error}</div>
        </div>
      </div>
    );
  }

  // Show progress if transcript is processing or not found
  if (status === "processing" || !transcript) {
    return (
      <div className="flex h-full flex-col">
        <div className="border-b p-4">
          <h3 className="font-semibold">Transcription Status</h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          <TranscriptionProgress
            videoId={videoId}
            onComplete={handleTranscriptComplete}
          />
        </div>
      </div>
    );
  }

  // Show transcript display
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Transcript</h3>
          <TranscriptExport videoId={videoId} />
        </div>
      </div>

      {/* Search */}
      <div className="border-b p-4">
        <TranscriptSearch onSearchChange={setSearchQuery} />
      </div>

      {/* Transcript content */}
      <div className="flex-1 overflow-hidden">
        <TranscriptDisplay
          transcript={transcript}
          currentTime={currentTime}
          onWordClick={onSeek}
          searchQuery={searchQuery}
        />
      </div>
    </div>
  );
}
