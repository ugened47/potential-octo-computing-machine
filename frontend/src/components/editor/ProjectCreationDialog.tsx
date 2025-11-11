'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RESOLUTION_PRESETS } from '@/types/advancedEditor';
import { advancedEditorAPI } from '@/lib/advanced-editor-api';
import { useToast } from '@/components/ui/use-toast';

interface ProjectCreationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated?: (projectId: string) => void;
}

export function ProjectCreationDialog({
  isOpen,
  onClose,
  onProjectCreated,
}: ProjectCreationDialogProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isCreating, setIsCreating] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    resolutionPreset: '1080p (Full HD)',
    customWidth: 1920,
    customHeight: 1080,
    frameRate: 30,
    duration: 60,
  });

  const selectedPreset = RESOLUTION_PRESETS.find((p) => p.name === formData.resolutionPreset);
  const isCustomResolution = formData.resolutionPreset === 'Custom';

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a project name',
        variant: 'destructive',
      });
      return;
    }

    const width = isCustomResolution ? formData.customWidth : selectedPreset!.width;
    const height = isCustomResolution ? formData.customHeight : selectedPreset!.height;

    if (width <= 0 || height <= 0) {
      toast({
        title: 'Error',
        description: 'Invalid resolution. Width and height must be positive',
        variant: 'destructive',
      });
      return;
    }

    if (formData.duration <= 0) {
      toast({
        title: 'Error',
        description: 'Duration must be greater than 0',
        variant: 'destructive',
      });
      return;
    }

    setIsCreating(true);

    try {
      const project = await advancedEditorAPI.createProject({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        width,
        height,
        frame_rate: formData.frameRate,
        duration: formData.duration,
      });

      toast({
        title: 'Success',
        description: 'Project created successfully',
      });

      onClose();

      if (onProjectCreated) {
        onProjectCreated(project.id);
      } else {
        router.push(`/editor/advanced/${project.id}`);
      }
    } catch (error) {
      console.error('Failed to create project:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create project',
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Set up your multi-track video editing project
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Project Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Project Name *</Label>
            <Input
              id="name"
              placeholder="My Awesome Video"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Input
              id="description"
              placeholder="A brief description of your project"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          {/* Resolution Preset */}
          <div className="space-y-2">
            <Label htmlFor="resolution">Resolution</Label>
            <Select
              value={formData.resolutionPreset}
              onValueChange={(value) => setFormData({ ...formData, resolutionPreset: value })}
            >
              <SelectTrigger id="resolution">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RESOLUTION_PRESETS.map((preset) => (
                  <SelectItem key={preset.name} value={preset.name}>
                    {preset.name} {preset.description && `- ${preset.description}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Custom Resolution */}
          {isCustomResolution && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="width">Width (px)</Label>
                <Input
                  id="width"
                  type="number"
                  min="1"
                  value={formData.customWidth}
                  onChange={(e) =>
                    setFormData({ ...formData, customWidth: parseInt(e.target.value) || 0 })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="height">Height (px)</Label>
                <Input
                  id="height"
                  type="number"
                  min="1"
                  value={formData.customHeight}
                  onChange={(e) =>
                    setFormData({ ...formData, customHeight: parseInt(e.target.value) || 0 })
                  }
                />
              </div>
            </div>
          )}

          {/* Frame Rate and Duration */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="framerate">Frame Rate (fps)</Label>
              <Select
                value={formData.frameRate.toString()}
                onValueChange={(value) => setFormData({ ...formData, frameRate: parseInt(value) })}
              >
                <SelectTrigger id="framerate">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24">24 fps</SelectItem>
                  <SelectItem value="30">30 fps</SelectItem>
                  <SelectItem value="60">60 fps</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration (seconds)</Label>
              <Input
                id="duration"
                type="number"
                min="1"
                value={formData.duration}
                onChange={(e) =>
                  setFormData({ ...formData, duration: parseInt(e.target.value) || 0 })
                }
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={isCreating}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            {isCreating ? 'Creating...' : 'Create Project'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
