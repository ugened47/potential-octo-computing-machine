/**
 * Comment Thread Component
 *
 * Displays a comment and its replies with actions.
 */

'use client';

import { useState } from 'react';
import type { CommentThread, CreateCommentRequest } from '@/types/collaboration';
import { createComment, updateComment, addCommentReaction } from '@/lib/api/collaboration';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  MessageSquare,
  MoreVertical,
  Trash,
  Edit,
  Check,
  Clock,
  Smile,
  Reply,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommentThreadComponentProps {
  thread: CommentThread;
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
  onResolve: (commentId: string) => void;
  onUnresolve: (commentId: string) => void;
  onDelete: (commentId: string) => void;
  onSeek?: (timestamp: number) => void;
}

export function CommentThreadComponent({
  thread,
  resourceType,
  resourceId,
  onResolve,
  onUnresolve,
  onDelete,
  onSeek,
}: CommentThreadComponentProps) {
  const [showReply, setShowReply] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const handleReply = async () => {
    if (!replyText.trim()) return;

    try {
      setIsSubmitting(true);
      const replyData: CreateCommentRequest = {
        resource_type: resourceType,
        resource_id: resourceId,
        content: replyText,
        parent_id: thread.parent.id,
      };

      await createComment(replyData);
      setReplyText('');
      setShowReply(false);
      // Parent component will reload comments
    } catch (error) {
      console.error('Failed to reply:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (commentId: string) => {
    if (!editText.trim()) return;

    try {
      await updateComment(commentId, { content: editText });
      setEditingId(null);
      setEditText('');
      // Parent component will reload comments
    } catch (error) {
      console.error('Failed to edit comment:', error);
    }
  };

  const handleReaction = async (commentId: string, emoji: string) => {
    try {
      await addCommentReaction(commentId, emoji);
      // Parent component will reload comments
    } catch (error) {
      console.error('Failed to add reaction:', error);
    }
  };

  const formatTimestamp = (seconds?: number) => {
    if (seconds === undefined) return null;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const renderComment = (comment: typeof thread.parent, isReply = false) => {
    const isEditing = editingId === comment.id;

    return (
      <div
        key={comment.id}
        className={cn(
          'p-3 rounded-lg border',
          isReply && 'ml-8 bg-muted/30',
          comment.resolved && 'opacity-60'
        )}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-xs font-medium">
                {comment.user?.name?.[0] || comment.user?.email[0].toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-sm font-medium">
                {comment.user?.name || comment.user?.email}
              </p>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <span>{formatDate(comment.created_at)}</span>
                {comment.edited && <span>(edited)</span>}
                {comment.timestamp !== undefined && (
                  <>
                    <span>•</span>
                    <button
                      onClick={() => onSeek?.(comment.timestamp!)}
                      className="flex items-center space-x-1 hover:text-primary"
                    >
                      <Clock className="h-3 w-3" />
                      <span>{formatTimestamp(comment.timestamp)}</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setEditingId(comment.id);
                  setEditText(comment.content);
                }}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              {!isReply && (
                <DropdownMenuItem
                  onClick={() =>
                    comment.resolved
                      ? onUnresolve(comment.id)
                      : onResolve(comment.id)
                  }
                >
                  <Check className="mr-2 h-4 w-4" />
                  {comment.resolved ? 'Unresolve' : 'Resolve'}
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={() => onDelete(comment.id)}
                className="text-destructive"
              >
                <Trash className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="min-h-[60px]"
            />
            <div className="flex space-x-2">
              <Button size="sm" onClick={() => handleEdit(comment.id)}>
                Save
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditingId(null);
                  setEditText('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-sm mb-2 whitespace-pre-wrap">{comment.content}</p>

            {/* Reactions */}
            {comment.reactions && comment.reactions.length > 0 && (
              <div className="flex items-center space-x-1 mb-2">
                {Object.entries(
                  comment.reactions.reduce((acc, r) => {
                    acc[r.emoji] = (acc[r.emoji] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([emoji, count]) => (
                  <Badge key={emoji} variant="secondary" className="text-xs">
                    {emoji} {count}
                  </Badge>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center space-x-2">
              {!isReply && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowReply(!showReply)}
                >
                  <Reply className="mr-1 h-3 w-3" />
                  Reply
                </Button>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <Smile className="mr-1 h-3 w-3" />
                    React
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  {['👍', '❤️', '😂', '🎉', '🤔', '👀'].map((emoji) => (
                    <DropdownMenuItem
                      key={emoji}
                      onClick={() => handleReaction(comment.id, emoji)}
                    >
                      {emoji}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
              {comment.resolved && (
                <Badge variant="secondary" className="ml-auto">
                  <Check className="mr-1 h-3 w-3" />
                  Resolved
                </Badge>
              )}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-2">
      {renderComment(thread.parent)}

      {/* Replies */}
      {thread.replies.map((reply) => renderComment(reply, true))}

      {/* Reply Form */}
      {showReply && (
        <div className="ml-8 space-y-2">
          <Textarea
            placeholder="Write a reply..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            className="min-h-[60px]"
          />
          <div className="flex space-x-2">
            <Button size="sm" onClick={handleReply} disabled={isSubmitting}>
              <Reply className="mr-1 h-3 w-3" />
              {isSubmitting ? 'Sending...' : 'Reply'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShowReply(false);
                setReplyText('');
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
