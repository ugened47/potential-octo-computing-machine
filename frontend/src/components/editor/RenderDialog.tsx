'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { QUALITY_PRESETS, type RenderConfig, type RenderQuality, type RenderFormat } from '@/types/advancedEditor';
import { advancedEditorAPI } from '@/lib/advanced-editor-api';
import { useToast } from '@/components/ui/use-toast';
import { Download, X } from 'lucide-react';

interface RenderDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function RenderDialog({ projectId, isOpen, onClose }: RenderDialogProps) {
  const { toast } = useToast();
  const [isRendering, setIsRendering] = useState(false);
  const [renderProgress, setRenderProgress] = useState(0);
  const [renderStage, setRenderStage] = useState('');
  const [renderJobId, setRenderJobId] = useState<string | null>(null);
  const [renderOutputUrl, setRenderOutputUrl] = useState<string | null>(null);

  const [quality, setQuality] = useState<RenderQuality>('high');
  const [format, setFormat] = useState<RenderFormat>('mp4');

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isRendering && renderJobId) {
      interval = setInterval(async () => {
        try {
          const progress = await advancedEditorAPI.getRenderProgress(projectId);
          setRenderProgress(progress.progress);
          setRenderStage(progress.stage);

          if (progress.status === 'completed') {
            setIsRendering(false);
            // Fetch the project to get render_output_url
            const project = await advancedEditorAPI.getProject(projectId);
            setRenderOutputUrl(project.render_output_url || null);
            toast({
              title: 'Success',
              description: 'Project rendered successfully',
            });
          } else if (progress.status === 'error') {
            setIsRendering(false);
            toast({
              title: 'Error',
              description: 'Render failed',
              variant: 'destructive',
            });
          }
        } catch (error) {
          console.error('Failed to get render progress:', error);
        }
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRendering, renderJobId, projectId, toast]);

  const handleRender = async () => {
    setIsRendering(true);
    setRenderProgress(0);
    setRenderStage('Starting render...');
    setRenderOutputUrl(null);

    const config: RenderConfig = {
      quality,
      format,
    };

    try {
      const response = await advancedEditorAPI.renderProject(projectId, config);
      setRenderJobId(response.job_id);
      toast({
        title: 'Render Started',
        description: `Estimated time: ${Math.round(response.estimated_time / 60)} minutes`,
      });
    } catch (error) {
      console.error('Failed to start render:', error);
      setIsRendering(false);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to start render',
        variant: 'destructive',
      });
    }
  };

  const handleCancelRender = async () => {
    try {
      await advancedEditorAPI.cancelRender(projectId);
      setIsRendering(false);
      setRenderJobId(null);
      toast({
        title: 'Render Cancelled',
        description: 'The render has been cancelled',
      });
    } catch (error) {
      console.error('Failed to cancel render:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel render',
        variant: 'destructive',
      });
    }
  };

  const handleDownload = () => {
    if (renderOutputUrl) {
      window.open(renderOutputUrl, '_blank');
    }
  };

  const handleClose = () => {
    if (!isRendering) {
      onClose();
      // Reset state after closing
      setTimeout(() => {
        setRenderProgress(0);
        setRenderStage('');
        setRenderJobId(null);
        setRenderOutputUrl(null);
      }, 300);
    }
  };

  const selectedPreset = QUALITY_PRESETS.find((p) => p.name === quality);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Render Project</DialogTitle>
          <DialogDescription>
            Export your multi-track composition to video
          </DialogDescription>
        </DialogHeader>

        {!isRendering && !renderOutputUrl ? (
          <div className="space-y-6 py-4">
            {/* Quality Preset */}
            <div className="space-y-2">
              <Label htmlFor="quality">Quality Preset</Label>
              <Select value={quality} onValueChange={(value) => setQuality(value as RenderQuality)}>
                <SelectTrigger id="quality">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUALITY_PRESETS.map((preset) => (
                    <SelectItem key={preset.name} value={preset.name}>
                      <div>
                        <div className="font-medium">{preset.label}</div>
                        <div className="text-xs text-muted-foreground">
                          {preset.resolution} • {preset.bitrate} • {preset.description}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Format */}
            <div className="space-y-2">
              <Label htmlFor="format">Output Format</Label>
              <Select value={format} onValueChange={(value) => setFormat(value as RenderFormat)}>
                <SelectTrigger id="format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mp4">MP4 (H.264)</SelectItem>
                  <SelectItem value="mov">MOV (QuickTime)</SelectItem>
                  <SelectItem value="webm">WebM (VP9)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Estimated Info */}
            {selectedPreset && (
              <div className="p-4 bg-muted rounded-lg space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Resolution:</span>
                  <span className="font-medium">{selectedPreset.resolution}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Bitrate:</span>
                  <span className="font-medium">{selectedPreset.bitrate}</span>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleRender}>Start Render</Button>
            </div>
          </div>
        ) : isRendering ? (
          <div className="space-y-6 py-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{renderStage}</span>
                <span className="font-medium">{Math.round(renderProgress)}%</span>
              </div>
              <Progress value={renderProgress} />
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleCancelRender}>
                <X className="w-4 h-4 mr-2" />
                Cancel Render
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="p-6 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
              <div className="text-green-600 dark:text-green-400 text-lg font-semibold mb-2">
                Render Complete!
              </div>
              <p className="text-sm text-muted-foreground">
                Your video has been successfully rendered
              </p>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button onClick={handleDownload}>
                <Download className="w-4 h-4 mr-2" />
                Download Video
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
