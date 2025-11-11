/**
 * Active Users Component
 *
 * Displays presence indicators for users currently viewing/editing a resource.
 */

'use client';

import { usePresence } from '@/hooks/useWebSocket';
import type { UserPresence } from '@/types/collaboration';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Users, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActiveUsersProps {
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
  maxDisplay?: number;
  showStatus?: boolean;
}

const statusColors = {
  online: 'bg-green-500',
  away: 'bg-yellow-500',
  offline: 'bg-gray-400',
};

const statusLabels = {
  online: 'Online',
  away: 'Away',
  offline: 'Offline',
};

export function ActiveUsers({
  resourceType,
  resourceId,
  maxDisplay = 5,
  showStatus = true,
}: ActiveUsersProps) {
  const { activeUsers, isConnected } = usePresence(resourceType, resourceId);

  const getInitials = (user: UserPresence['user']): string => {
    if (user.name) {
      return user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return user.email[0].toUpperCase();
  };

  const formatLastSeen = (lastSeen: string): string => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  if (!isConnected || activeUsers.length === 0) {
    return null;
  }

  const displayedUsers = activeUsers.slice(0, maxDisplay);
  const remainingCount = activeUsers.length - maxDisplay;

  return (
    <TooltipProvider>
      <div className="flex items-center space-x-2">
        <div className="flex items-center -space-x-2">
          {displayedUsers.map((presence) => (
            <Tooltip key={presence.user_id}>
              <TooltipTrigger asChild>
                <div className="relative">
                  <Avatar className="h-8 w-8 border-2 border-background hover:z-10 cursor-pointer transition-transform hover:scale-110">
                    <AvatarImage
                      src={presence.user.avatar_url}
                      alt={presence.user.name || presence.user.email}
                    />
                    <AvatarFallback className="text-xs">
                      {getInitials(presence.user)}
                    </AvatarFallback>
                  </Avatar>
                  {showStatus && (
                    <Circle
                      className={cn(
                        'absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background',
                        statusColors[presence.status]
                      )}
                      fill="currentColor"
                    />
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <div className="space-y-1">
                  <p className="font-medium">
                    {presence.user.name || presence.user.email}
                  </p>
                  {showStatus && (
                    <p className="text-xs text-muted-foreground">
                      {statusLabels[presence.status]}
                      {presence.status !== 'online' &&
                        ` • ${formatLastSeen(presence.last_seen)}`}
                    </p>
                  )}
                  {presence.current_resource && (
                    <p className="text-xs text-muted-foreground">
                      Viewing {presence.current_resource.type}
                    </p>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          ))}

          {remainingCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="h-8 w-8 rounded-full border-2 border-background bg-muted flex items-center justify-center cursor-pointer hover:z-10 transition-transform hover:scale-110">
                  <span className="text-xs font-medium">+{remainingCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <div className="space-y-1">
                  {activeUsers.slice(maxDisplay).map((presence) => (
                    <p key={presence.user_id} className="text-sm">
                      {presence.user.name || presence.user.email}
                    </p>
                  ))}
                </div>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {activeUsers.length > 0 && (
          <Badge variant="secondary" className="text-xs">
            <Users className="mr-1 h-3 w-3" />
            {activeUsers.length} {activeUsers.length === 1 ? 'user' : 'users'}
          </Badge>
        )}
      </div>
    </TooltipProvider>
  );
}

/**
 * Compact version for toolbar/header
 */
export function ActiveUsersCompact({
  resourceType,
  resourceId,
}: {
  resourceType: 'video' | 'project' | 'clip';
  resourceId: string;
}) {
  const { activeUsers } = usePresence(resourceType, resourceId);

  if (activeUsers.length === 0) {
    return null;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center space-x-1 px-2 py-1 rounded-md bg-muted cursor-pointer hover:bg-muted/80">
            <Circle className="h-2 w-2 fill-green-500 text-green-500" />
            <span className="text-xs font-medium">{activeUsers.length}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <p className="font-medium text-sm">Active Users</p>
            {activeUsers.map((presence) => (
              <p key={presence.user_id} className="text-xs">
                {presence.user.name || presence.user.email}
              </p>
            ))}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
