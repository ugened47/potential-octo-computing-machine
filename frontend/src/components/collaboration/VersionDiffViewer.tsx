/**
 * Version Diff Viewer Component
 *
 * Displays differences between two versions.
 */

'use client';

import { useState, useEffect } from 'react';
import type { VersionDiff, VersionChange } from '@/types/collaboration';
import { compareVersions } from '@/lib/api/collaboration';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Plus, Minus, Edit, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VersionDiffViewerProps {
  versionFromId: string;
  versionToId: string;
}

const changeTypeColors = {
  added: 'bg-green-100 text-green-800 border-green-300',
  removed: 'bg-red-100 text-red-800 border-red-300',
  modified: 'bg-blue-100 text-blue-800 border-blue-300',
};

const changeTypeIcons = {
  added: Plus,
  removed: Minus,
  modified: Edit,
};

export function VersionDiffViewer({
  versionFromId,
  versionToId,
}: VersionDiffViewerProps) {
  const [diff, setDiff] = useState<VersionDiff | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDiff();
  }, [versionFromId, versionToId]);

  const loadDiff = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const versionDiff = await compareVersions(versionFromId, versionToId);
      setDiff(versionDiff);
    } catch (err) {
      console.error('Failed to load diff:', err);
      setError('Failed to compare versions');
    } finally {
      setIsLoading(false);
    }
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const renderChange = (change: VersionChange) => {
    const Icon = changeTypeIcons[change.type];

    return (
      <div
        key={change.path}
        className={cn(
          'p-3 rounded-lg border mb-2',
          change.type === 'added' && 'bg-green-50/50',
          change.type === 'removed' && 'bg-red-50/50',
          change.type === 'modified' && 'bg-blue-50/50'
        )}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Icon className="h-4 w-4" />
            <code className="text-sm font-mono">{change.path}</code>
          </div>
          <Badge variant="outline" className={changeTypeColors[change.type]}>
            {change.type}
          </Badge>
        </div>

        {change.description && (
          <p className="text-sm text-muted-foreground mb-2">
            {change.description}
          </p>
        )}

        {change.type === 'modified' && (
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Before:</p>
              <pre className="text-xs bg-red-50 p-2 rounded border border-red-200 overflow-x-auto">
                {formatValue(change.old_value)}
              </pre>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">After:</p>
              <pre className="text-xs bg-green-50 p-2 rounded border border-green-200 overflow-x-auto">
                {formatValue(change.new_value)}
              </pre>
            </div>
          </div>
        )}

        {change.type === 'added' && change.new_value && (
          <div className="mt-2">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Added value:
            </p>
            <pre className="text-xs bg-green-50 p-2 rounded border border-green-200 overflow-x-auto">
              {formatValue(change.new_value)}
            </pre>
          </div>
        )}

        {change.type === 'removed' && change.old_value && (
          <div className="mt-2">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Removed value:
            </p>
            <pre className="text-xs bg-red-50 p-2 rounded border border-red-200 overflow-x-auto">
              {formatValue(change.old_value)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <p className="text-muted-foreground">Loading comparison...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-destructive mb-2" />
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (!diff) {
    return null;
  }

  return (
    <div className="p-4 space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">
          Comparing v{diff.version_from} → v{diff.version_to}
        </h4>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="bg-green-50">
            <Plus className="mr-1 h-3 w-3" />
            {diff.changes.filter((c) => c.type === 'added').length} added
          </Badge>
          <Badge variant="outline" className="bg-blue-50">
            <Edit className="mr-1 h-3 w-3" />
            {diff.changes.filter((c) => c.type === 'modified').length} modified
          </Badge>
          <Badge variant="outline" className="bg-red-50">
            <Minus className="mr-1 h-3 w-3" />
            {diff.changes.filter((c) => c.type === 'removed').length} removed
          </Badge>
        </div>
      </div>

      {diff.summary && (
        <p className="text-sm text-muted-foreground">{diff.summary}</p>
      )}

      {/* Changes List */}
      <ScrollArea className="max-h-[400px]">
        {diff.changes.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">
            No changes detected between these versions.
          </p>
        ) : (
          <div className="space-y-2">
            {diff.changes.map((change, index) => (
              <div key={`${change.path}-${index}`}>{renderChange(change)}</div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
