'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Clock, Settings, Trash2, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { advancedEditorAPI } from '@/lib/advanced-editor-api';
import { ProjectCreationDialog } from './ProjectCreationDialog';
import type { Project, ProjectStatus } from '@/types/advancedEditor';
import { useToast } from '@/components/ui/use-toast';

const STATUS_COLORS: Record<ProjectStatus, string> = {
  draft: 'bg-gray-500',
  rendering: 'bg-blue-500',
  completed: 'bg-green-500',
  error: 'bg-red-500',
};

const STATUS_LABELS: Record<ProjectStatus, string> = {
  draft: 'Draft',
  rendering: 'Rendering',
  completed: 'Completed',
  error: 'Error',
};

export function ProjectsList() {
  const router = useRouter();
  const { toast } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const response = await advancedEditorAPI.getProjects({
        limit: 50,
        sort: 'created_at',
      });
      setProjects(response.projects);
    } catch (error) {
      console.error('Failed to load projects:', error);
      toast({
        title: 'Error',
        description: 'Failed to load projects',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenProject = (projectId: string) => {
    router.push(`/editor/advanced/${projectId}`);
  };

  const handleDuplicateProject = async (projectId: string, projectName: string) => {
    try {
      const newProject = await advancedEditorAPI.duplicateProject(projectId);
      toast({
        title: 'Success',
        description: `Duplicated "${projectName}"`,
      });
      setProjects((prev) => [newProject, ...prev]);
    } catch (error) {
      console.error('Failed to duplicate project:', error);
      toast({
        title: 'Error',
        description: 'Failed to duplicate project',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!confirm(`Are you sure you want to delete "${projectName}"?`)) {
      return;
    }

    try {
      await advancedEditorAPI.deleteProject(projectId);
      toast({
        title: 'Success',
        description: `Deleted "${projectName}"`,
      });
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (error) {
      console.error('Failed to delete project:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete project',
        variant: 'destructive',
      });
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Advanced Editor Projects</h1>
          <p className="text-muted-foreground mt-1">
            Create and manage multi-track video compositions
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)} size="lg">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <Card className="p-12 text-center">
          <Settings className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-xl font-semibold mb-2">No projects yet</h3>
          <p className="text-muted-foreground mb-6">
            Create your first multi-track video project to get started
          </p>
          <Button onClick={() => setIsCreateDialogOpen(true)} size="lg">
            <Plus className="w-4 h-4 mr-2" />
            Create Your First Project
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleOpenProject(project.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="truncate">{project.name}</CardTitle>
                    <CardDescription className="line-clamp-2 mt-1">
                      {project.description || 'No description'}
                    </CardDescription>
                  </div>
                  <Badge className={`${STATUS_COLORS[project.status]} ml-2`}>
                    {STATUS_LABELS[project.status]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {project.thumbnail_url && (
                  <img
                    src={project.thumbnail_url}
                    alt={project.name}
                    className="w-full h-32 object-cover rounded mb-4"
                  />
                )}
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Resolution:</span>
                    <span className="font-medium text-foreground">
                      {project.width}x{project.height}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Duration:</span>
                    <span className="font-medium text-foreground">
                      {formatDuration(project.duration_seconds)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Frame Rate:</span>
                    <span className="font-medium text-foreground">
                      {project.frame_rate} fps
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs">
                    <Clock className="w-3 h-3" />
                    <span>{formatDate(project.updated_at)}</span>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicateProject(project.id, project.name);
                    }}
                  >
                    <Copy className="w-3 h-3 mr-1" />
                    Duplicate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteProject(project.id, project.name);
                    }}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ProjectCreationDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onProjectCreated={() => {
          loadProjects();
        }}
      />
    </div>
  );
}
