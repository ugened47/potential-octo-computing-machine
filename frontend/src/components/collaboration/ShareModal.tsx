/**
 * Share Modal Component
 *
 * Allows users to share resources with team members or via link.
 */

'use client';

import { useState, useEffect } from 'react';
import type {
  Share,
  CreateShareRequest,
  PermissionLevel,
  User,
} from '@/types/collaboration';
import {
  getShares,
  createShare,
  deleteShare,
} from '@/lib/api/collaboration';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ShareLinkGenerator } from './ShareLinkGenerator';
import { AccessControlSelect } from './AccessControlSelect';
import { Users, Link as LinkIcon, Trash, Check, Mail } from 'lucide-react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
  resourceTitle?: string;
}

export function ShareModal({
  isOpen,
  onClose,
  resourceType,
  resourceId,
  resourceTitle,
}: ShareModalProps) {
  const [shares, setShares] = useState<Share[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [permissionLevel, setPermissionLevel] = useState<PermissionLevel>('view' as PermissionLevel);
  const [message, setMessage] = useState('');
  const [isSharing, setIsSharing] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadShares();
    }
  }, [isOpen, resourceType, resourceId]);

  const loadShares = async () => {
    try {
      setIsLoading(true);
      const existingShares = await getShares(resourceType, resourceId);
      setShares(existingShares);
    } catch (error) {
      console.error('Failed to load shares:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = async () => {
    if (!email) return;

    try {
      setIsSharing(true);
      const shareData: CreateShareRequest = {
        resource_type: resourceType,
        resource_id: resourceId,
        user_id: email, // In real implementation, this would be user ID lookup
        permission_level: permissionLevel,
        message,
      };

      const newShare = await createShare(shareData);
      setShares((prev) => [...prev, newShare]);
      setEmail('');
      setMessage('');
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to share:', error);
    } finally {
      setIsSharing(false);
    }
  };

  const handleRemoveShare = async (shareId: string) => {
    try {
      await deleteShare(shareId);
      setShares((prev) => prev.filter((s) => s.id !== shareId));
    } catch (error) {
      console.error('Failed to remove share:', error);
    }
  };

  const getPermissionBadge = (level: PermissionLevel) => {
    const colors: Record<PermissionLevel, string> = {
      view: 'bg-gray-100 text-gray-800',
      comment: 'bg-blue-100 text-blue-800',
      edit: 'bg-green-100 text-green-800',
      admin: 'bg-purple-100 text-purple-800',
    };

    return (
      <Badge variant="outline" className={colors[level]}>
        {level}
      </Badge>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Share {resourceTitle || 'Resource'}</DialogTitle>
          <DialogDescription>
            Invite people to collaborate or generate a shareable link.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="people" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="people">
              <Users className="mr-2 h-4 w-4" />
              Share with People
            </TabsTrigger>
            <TabsTrigger value="link">
              <LinkIcon className="mr-2 h-4 w-4" />
              Share via Link
            </TabsTrigger>
          </TabsList>

          <TabsContent value="people" className="space-y-4">
            {/* Share Form */}
            <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="flex space-x-2">
                  <Input
                    id="email"
                    type="email"
                    placeholder="colleague@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleShare();
                      }
                    }}
                  />
                  <AccessControlSelect
                    value={permissionLevel}
                    onChange={setPermissionLevel}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message (Optional)</Label>
                <Input
                  id="message"
                  placeholder="Add a personal message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>

              <Button
                onClick={handleShare}
                disabled={!email || isSharing}
                className="w-full"
              >
                {shareSuccess ? (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Shared!
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    {isSharing ? 'Sending...' : 'Send Invitation'}
                  </>
                )}
              </Button>
            </div>

            {/* Existing Shares */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">People with access</h4>
              {isLoading ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : shares.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  No one has access yet. Share to get started.
                </p>
              ) : (
                <div className="space-y-2">
                  {shares.map((share) => (
                    <div
                      key={share.id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-sm font-medium">
                            {share.shared_with_user?.name?.[0] ||
                              share.shared_with_user?.email[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm font-medium">
                            {share.shared_with_user?.name || 'Unknown'}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {share.shared_with_user?.email}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getPermissionBadge(share.permission_level)}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveShare(share.id)}
                        >
                          <Trash className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="link" className="space-y-4">
            <ShareLinkGenerator
              resourceType={resourceType}
              resourceId={resourceId}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
