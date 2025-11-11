/**
 * Share Link Generator Component
 *
 * Generates and manages shareable links with access control.
 */

'use client';

import { useState, useEffect } from 'react';
import type {
  ShareLink,
  CreateShareLinkRequest,
  ShareLinkAccess,
  PermissionLevel,
} from '@/types/collaboration';
import {
  getShareLinks,
  createShareLink,
  deleteShareLink,
} from '@/lib/api/collaboration';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { AccessControlSelect } from './AccessControlSelect';
import { Copy, Trash, Check, Link as LinkIcon, Lock, Globe } from 'lucide-react';

interface ShareLinkGeneratorProps {
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
}

export function ShareLinkGenerator({
  resourceType,
  resourceId,
}: ShareLinkGeneratorProps) {
  const [links, setLinks] = useState<ShareLink[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [copiedLinkId, setCopiedLinkId] = useState<string | null>(null);

  const [linkConfig, setLinkConfig] = useState<CreateShareLinkRequest>({
    resource_type: resourceType,
    resource_id: resourceId,
    access: 'anyone_with_link' as ShareLinkAccess,
    permission_level: 'view' as PermissionLevel,
    password: '',
    max_uses: undefined,
    expires_at: undefined,
  });

  useEffect(() => {
    loadLinks();
  }, [resourceType, resourceId]);

  const loadLinks = async () => {
    try {
      setIsLoading(true);
      const existingLinks = await getShareLinks(resourceType, resourceId);
      setLinks(existingLinks);
    } catch (error) {
      console.error('Failed to load share links:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateLink = async () => {
    try {
      setIsCreating(true);
      const newLink = await createShareLink(linkConfig);
      setLinks((prev) => [...prev, newLink]);
      // Reset config
      setLinkConfig({
        ...linkConfig,
        password: '',
        max_uses: undefined,
        expires_at: undefined,
      });
      setShowAdvanced(false);
    } catch (error) {
      console.error('Failed to create share link:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteLink = async (linkId: string) => {
    try {
      await deleteShareLink(linkId);
      setLinks((prev) => prev.filter((l) => l.id !== linkId));
    } catch (error) {
      console.error('Failed to delete share link:', error);
    }
  };

  const copyToClipboard = async (link: ShareLink) => {
    const url = `${window.location.origin}/shared/${link.token}`;
    await navigator.clipboard.writeText(url);
    setCopiedLinkId(link.id);
    setTimeout(() => setCopiedLinkId(null), 2000);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-4">
      {/* Create Link Section */}
      <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
        <div className="space-y-2">
          <Label>Access Level</Label>
          <Select
            value={linkConfig.access}
            onValueChange={(value) =>
              setLinkConfig({ ...linkConfig, access: value as ShareLinkAccess })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="private">
                <div className="flex items-center space-x-2">
                  <Lock className="h-4 w-4" />
                  <span>Private - Only invited people</span>
                </div>
              </SelectItem>
              <SelectItem value="anyone_with_link">
                <div className="flex items-center space-x-2">
                  <LinkIcon className="h-4 w-4" />
                  <span>Anyone with the link</span>
                </div>
              </SelectItem>
              <SelectItem value="public">
                <div className="flex items-center space-x-2">
                  <Globe className="h-4 w-4" />
                  <span>Public - Anyone can access</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Permission Level</Label>
          <AccessControlSelect
            value={linkConfig.permission_level}
            onChange={(value) =>
              setLinkConfig({ ...linkConfig, permission_level: value })
            }
          />
        </div>

        {/* Advanced Options */}
        <div className="flex items-center space-x-2">
          <Switch
            checked={showAdvanced}
            onCheckedChange={setShowAdvanced}
            id="advanced"
          />
          <Label htmlFor="advanced" className="cursor-pointer">
            Advanced options
          </Label>
        </div>

        {showAdvanced && (
          <div className="space-y-3 pt-2">
            <div className="space-y-2">
              <Label htmlFor="password">Password Protection (Optional)</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter password"
                value={linkConfig.password || ''}
                onChange={(e) =>
                  setLinkConfig({ ...linkConfig, password: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-uses">Max Uses (Optional)</Label>
              <Input
                id="max-uses"
                type="number"
                placeholder="Unlimited"
                value={linkConfig.max_uses || ''}
                onChange={(e) =>
                  setLinkConfig({
                    ...linkConfig,
                    max_uses: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="expires">Expiration Date (Optional)</Label>
              <Input
                id="expires"
                type="datetime-local"
                value={linkConfig.expires_at || ''}
                onChange={(e) =>
                  setLinkConfig({ ...linkConfig, expires_at: e.target.value })
                }
              />
            </div>
          </div>
        )}

        <Button
          onClick={handleCreateLink}
          disabled={isCreating}
          className="w-full"
        >
          <LinkIcon className="mr-2 h-4 w-4" />
          {isCreating ? 'Creating...' : 'Generate Link'}
        </Button>
      </div>

      {/* Existing Links */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold">Active Links</h4>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : links.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No active links. Generate one to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {links.map((link) => {
              const url = `${window.location.origin}/shared/${link.token}`;
              const isCopied = copiedLinkId === link.id;

              return (
                <div
                  key={link.id}
                  className="p-3 border rounded-lg space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {link.access === 'public' ? (
                        <Globe className="h-4 w-4 text-muted-foreground" />
                      ) : link.password ? (
                        <Lock className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <LinkIcon className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="text-sm font-medium">
                        {link.access.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(link)}
                      >
                        {isCopied ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteLink(link.id)}
                      >
                        <Trash className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <Input
                      value={url}
                      readOnly
                      className="text-xs"
                      onClick={(e) => e.currentTarget.select()}
                    />
                  </div>

                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <span>
                      Permission: <strong>{link.permission_level}</strong>
                    </span>
                    {link.max_uses && (
                      <span>
                        Uses: {link.use_count}/{link.max_uses}
                      </span>
                    )}
                    <span>Expires: {formatDate(link.expires_at)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
