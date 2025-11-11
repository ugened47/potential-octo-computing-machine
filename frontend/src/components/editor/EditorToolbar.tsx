"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SilenceRemovalModal } from "./SilenceRemovalModal";
import { KeywordSearchPanel } from "./KeywordSearchPanel";
import { ClipsList } from "./ClipsList";
import { VolumeX, Scissors, FileVideo } from "lucide-react";
import type { Video } from "@/types/video";

interface EditorToolbarProps {
  video: Video;
}

export function EditorToolbar({ video }: EditorToolbarProps) {
  const [silenceModalOpen, setSilenceModalOpen] = useState(false);
  const [clipsRefreshTrigger, setClipsRefreshTrigger] = useState(0);

  const handleSilenceRemovalComplete = (outputVideoId: string) => {
    // Optionally refresh the page or update the video
    // Output video ID is available if needed: outputVideoId
  };

  const handleClipCreated = () => {
    // Trigger clips list refresh
    setClipsRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="border-t bg-background">
      <div className="p-4">
        <Tabs defaultValue="clips" className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList>
              <TabsTrigger value="clips" className="flex items-center gap-2">
                <FileVideo className="h-4 w-4" />
                Clips
              </TabsTrigger>
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Scissors className="h-4 w-4" />
                Search & Create
              </TabsTrigger>
            </TabsList>

            <Button
              variant="outline"
              onClick={() => setSilenceModalOpen(true)}
              className="flex items-center gap-2"
            >
              <VolumeX className="h-4 w-4" />
              Remove Silence
            </Button>
          </div>

          <TabsContent value="clips" className="mt-0">
            <ClipsList
              videoId={video.id}
              refreshTrigger={clipsRefreshTrigger}
            />
          </TabsContent>

          <TabsContent value="search" className="mt-0">
            <KeywordSearchPanel
              videoId={video.id}
              onClipCreated={handleClipCreated}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Silence Removal Modal */}
      <SilenceRemovalModal
        videoId={video.id}
        open={silenceModalOpen}
        onClose={() => setSilenceModalOpen(false)}
        onComplete={handleSilenceRemovalComplete}
      />
    </div>
  );
}
