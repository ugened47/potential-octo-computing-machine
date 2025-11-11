/**
 * Comments Panel Component
 *
 * Displays and manages comments on a resource with real-time updates.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import type { Comment, CommentThread, CreateCommentRequest } from '@/types/collaboration';
import {
  getCommentThreads,
  createComment,
  deleteComment,
  resolveComment,
  unresolveComment,
} from '@/lib/api/collaboration';
import { useRealtimeComments, useTypingIndicator } from '@/hooks/useWebSocket';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { CommentThreadComponent } from './CommentThread';
import { MessageSquare, Send, Filter } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface CommentsPanelProps {
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
  currentTimestamp?: number;
  onSeek?: (timestamp: number) => void;
}

type FilterType = 'all' | 'resolved' | 'unresolved';

export function CommentsPanel({
  resourceType,
  resourceId,
  currentTimestamp,
  onSeek,
}: CommentsPanelProps) {
  const [threads, setThreads] = useState<CommentThread[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [filter, setFilter] = useState<FilterType>('all');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Real-time updates
  const { typingUsers, sendTypingIndicator } = useTypingIndicator(
    resourceType,
    resourceId
  );

  useRealtimeComments(
    resourceType,
    resourceId,
    (comment) => {
      // Add new comment to threads
      loadComments();
    },
    (comment) => {
      // Update comment in threads
      loadComments();
    },
    (commentId) => {
      // Remove comment from threads
      setThreads((prev) =>
        prev
          .map((thread) => ({
            ...thread,
            replies: thread.replies.filter((r) => r.id !== commentId),
          }))
          .filter((thread) => thread.parent.id !== commentId)
      );
    }
  );

  useEffect(() => {
    loadComments();
  }, [resourceType, resourceId]);

  const loadComments = async () => {
    try {
      setIsLoading(true);
      const commentThreads = await getCommentThreads(resourceType, resourceId);
      setThreads(commentThreads);
    } catch (error) {
      console.error('Failed to load comments:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!newComment.trim()) return;

    try {
      setIsSubmitting(true);
      const commentData: CreateCommentRequest = {
        resource_type: resourceType,
        resource_id: resourceId,
        content: newComment,
        timestamp: currentTimestamp,
      };

      await createComment(commentData);
      setNewComment('');
      sendTypingIndicator(false);
      await loadComments();
    } catch (error) {
      console.error('Failed to create comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTyping = (value: string) => {
    setNewComment(value);
    if (value.length > 0) {
      sendTypingIndicator(true);
    } else {
      sendTypingIndicator(false);
    }
  };

  const handleResolve = async (commentId: string) => {
    try {
      await resolveComment(commentId);
      await loadComments();
    } catch (error) {
      console.error('Failed to resolve comment:', error);
    }
  };

  const handleUnresolve = async (commentId: string) => {
    try {
      await unresolveComment(commentId);
      await loadComments();
    } catch (error) {
      console.error('Failed to unresolve comment:', error);
    }
  };

  const handleDelete = async (commentId: string) => {
    if (!confirm('Are you sure you want to delete this comment?')) {
      return;
    }

    try {
      await deleteComment(commentId);
      await loadComments();
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  const filteredThreads = threads.filter((thread) => {
    if (filter === 'resolved') return thread.parent.resolved;
    if (filter === 'unresolved') return !thread.parent.resolved;
    return true;
  });

  const unresolvedCount = threads.filter((t) => !t.parent.resolved).length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <h3 className="font-semibold">Comments</h3>
            {unresolvedCount > 0 && (
              <Badge variant="secondary">{unresolvedCount} open</Badge>
            )}
          </div>
          <Select value={filter} onValueChange={(v) => setFilter(v as FilterType)}>
            <SelectTrigger className="w-[130px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="unresolved">Open</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* New Comment Input */}
        <div className="space-y-2">
          <Textarea
            ref={textareaRef}
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => handleTyping(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                handleSubmit();
              }
            }}
            className="min-h-[80px]"
          />
          {currentTimestamp !== undefined && (
            <p className="text-xs text-muted-foreground">
              Comment at {Math.floor(currentTimestamp / 60)}:
              {String(Math.floor(currentTimestamp % 60)).padStart(2, '0')}
            </p>
          )}
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              {typingUsers.length > 0 && (
                <span>
                  {typingUsers.map((t) => t.user.name || t.user.email).join(', ')}{' '}
                  {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </span>
              )}
            </div>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!newComment.trim() || isSubmitting}
            >
              <Send className="mr-2 h-4 w-4" />
              {isSubmitting ? 'Sending...' : 'Comment'}
            </Button>
          </div>
        </div>
      </div>

      {/* Comments List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {isLoading ? (
            <p className="text-center text-muted-foreground py-8">
              Loading comments...
            </p>
          ) : filteredThreads.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                {filter === 'all'
                  ? 'No comments yet. Start the conversation!'
                  : filter === 'resolved'
                  ? 'No resolved comments.'
                  : 'No open comments.'}
              </p>
            </div>
          ) : (
            filteredThreads.map((thread) => (
              <CommentThreadComponent
                key={thread.parent.id}
                thread={thread}
                resourceType={resourceType}
                resourceId={resourceId}
                onResolve={handleResolve}
                onUnresolve={handleUnresolve}
                onDelete={handleDelete}
                onSeek={onSeek}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
