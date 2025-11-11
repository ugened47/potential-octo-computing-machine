/**
 * Version History Component
 *
 * Displays version history with restore and compare functionality.
 */

'use client';

import { useState, useEffect } from 'react';
import type { Version, PaginatedResponse } from '@/types/collaboration';
import { getVersions, restoreVersion, deleteVersion } from '@/lib/api/collaboration';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { VersionDiffViewer } from './VersionDiffViewer';
import {
  History,
  RotateCcw,
  MoreVertical,
  Trash,
  GitCompare,
  Clock,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface VersionHistoryProps {
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
  currentVersion?: number;
  onRestore?: (version: Version) => void;
}

export function VersionHistory({
  resourceType,
  resourceId,
  currentVersion,
  onRestore,
}: VersionHistoryProps) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState<[string, string] | null>(
    null
  );
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
  });

  useEffect(() => {
    loadVersions();
  }, [resourceType, resourceId, pagination.page]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const response: PaginatedResponse<Version> = await getVersions(
        resourceType,
        resourceId,
        pagination.page,
        pagination.pageSize
      );
      setVersions(response.items);
      setPagination((prev) => ({ ...prev, total: response.total }));
    } catch (error) {
      console.error('Failed to load versions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = async (version: Version) => {
    if (
      !confirm(
        `Are you sure you want to restore to version ${version.version_number}?`
      )
    ) {
      return;
    }

    try {
      const restored = await restoreVersion(version.id);
      await loadVersions();
      onRestore?.(restored);
    } catch (error) {
      console.error('Failed to restore version:', error);
    }
  };

  const handleDelete = async (versionId: string) => {
    if (!confirm('Are you sure you want to delete this version?')) {
      return;
    }

    try {
      await deleteVersion(versionId);
      await loadVersions();
    } catch (error) {
      console.error('Failed to delete version:', error);
    }
  };

  const handleCompare = (version: Version) => {
    if (!selectedVersions) {
      // Select first version
      setSelectedVersions([version.id, '']);
    } else if (!selectedVersions[1]) {
      // Select second version
      setSelectedVersions([selectedVersions[0], version.id]);
    } else {
      // Reset and select new first version
      setSelectedVersions([version.id, '']);
    }
  };

  const handleClearComparison = () => {
    setSelectedVersions(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <History className="h-5 w-5" />
            <h3 className="font-semibold">Version History</h3>
            <Badge variant="secondary">{pagination.total} versions</Badge>
          </div>
          {selectedVersions && selectedVersions[1] && (
            <Button variant="outline" size="sm" onClick={handleClearComparison}>
              Clear Comparison
            </Button>
          )}
        </div>
        {selectedVersions && !selectedVersions[1] && (
          <p className="text-xs text-muted-foreground mt-2">
            Select another version to compare
          </p>
        )}
      </div>

      {/* Version List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {isLoading ? (
            <p className="text-center text-muted-foreground py-8">
              Loading versions...
            </p>
          ) : versions.length === 0 ? (
            <div className="text-center py-8">
              <History className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">No version history available.</p>
            </div>
          ) : (
            versions.map((version) => {
              const isSelected =
                selectedVersions?.includes(version.id) || false;
              const isCurrent = version.version_number === currentVersion;

              return (
                <div
                  key={version.id}
                  className={cn(
                    'p-4 border rounded-lg hover:shadow-sm transition-shadow',
                    isSelected && 'ring-2 ring-primary',
                    isCurrent && 'bg-primary/5 border-primary'
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-sm font-bold">
                          v{version.version_number}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <p className="font-medium">
                            Version {version.version_number}
                          </p>
                          {isCurrent && (
                            <Badge variant="default">Current</Badge>
                          )}
                          {version.metadata?.auto_saved && (
                            <Badge variant="secondary">Auto-saved</Badge>
                          )}
                        </div>
                        {version.description && (
                          <p className="text-sm text-muted-foreground">
                            {version.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleRestore(version)}>
                          <RotateCcw className="mr-2 h-4 w-4" />
                          Restore
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleCompare(version)}>
                          <GitCompare className="mr-2 h-4 w-4" />
                          Compare
                        </DropdownMenuItem>
                        {!isCurrent && (
                          <DropdownMenuItem
                            onClick={() => handleDelete(version.id)}
                            className="text-destructive"
                          >
                            <Trash className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <User className="h-3 w-3" />
                      <span>
                        {version.created_by?.name || version.created_by?.email}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>{formatDate(version.created_at)}</span>
                    </div>
                    {version.metadata?.file_size && (
                      <span>{formatFileSize(version.metadata.file_size)}</span>
                    )}
                    {version.metadata?.duration && (
                      <span>
                        {Math.floor(version.metadata.duration / 60)}:
                        {String(Math.floor(version.metadata.duration % 60)).padStart(
                          2,
                          '0'
                        )}
                      </span>
                    )}
                  </div>

                  {version.metadata?.changes_summary && (
                    <p className="text-xs text-muted-foreground mt-2">
                      {version.metadata.changes_summary}
                    </p>
                  )}

                  {isSelected && (
                    <div className="mt-2">
                      <Badge variant="outline" className="bg-primary/10">
                        <GitCompare className="mr-1 h-3 w-3" />
                        Selected for comparison
                      </Badge>
                    </div>
                  )}
                </div>
              );
            })
          )}

          {/* Pagination */}
          {pagination.total > pagination.pageSize && (
            <div className="flex items-center justify-center space-x-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.page === 1}
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page - 1 }))
                }
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {pagination.page} of{' '}
                {Math.ceil(pagination.total / pagination.pageSize)}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={
                  pagination.page >=
                  Math.ceil(pagination.total / pagination.pageSize)
                }
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page + 1 }))
                }
              >
                Next
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Diff Viewer */}
      {selectedVersions && selectedVersions[1] && (
        <div className="border-t">
          <VersionDiffViewer
            versionFromId={selectedVersions[0]}
            versionToId={selectedVersions[1]}
          />
        </div>
      )}
    </div>
  );
}
