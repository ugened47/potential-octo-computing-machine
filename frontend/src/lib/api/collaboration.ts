/**
 * Team Collaboration API Client
 *
 * API functions for organizations, team members, permissions, sharing,
 * comments, versions, and notifications.
 */

import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  TeamMember,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  Permission,
  GrantPermissionRequest,
  PermissionCheck,
  Share,
  ShareLink,
  CreateShareRequest,
  CreateShareLinkRequest,
  Comment,
  CommentThread,
  CreateCommentRequest,
  UpdateCommentRequest,
  Version,
  CreateVersionRequest,
  VersionDiff,
  Notification,
  NotificationPreferences,
  MarkNotificationReadRequest,
  PaginatedResponse,
} from '@/types/collaboration';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Helper function to make authenticated API requests
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'An error occurred',
    }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Organization API
// ============================================================================

/**
 * Get all organizations for the current user
 */
export async function getOrganizations(): Promise<Organization[]> {
  return apiRequest<Organization[]>('/api/organizations');
}

/**
 * Get a specific organization by ID
 */
export async function getOrganization(orgId: string): Promise<Organization> {
  return apiRequest<Organization>(`/api/organizations/${orgId}`);
}

/**
 * Create a new organization
 */
export async function createOrganization(
  data: CreateOrganizationRequest
): Promise<Organization> {
  return apiRequest<Organization>('/api/organizations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an organization
 */
export async function updateOrganization(
  orgId: string,
  data: UpdateOrganizationRequest
): Promise<Organization> {
  return apiRequest<Organization>(`/api/organizations/${orgId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete an organization
 */
export async function deleteOrganization(orgId: string): Promise<void> {
  return apiRequest<void>(`/api/organizations/${orgId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Team Member API
// ============================================================================

/**
 * Get all members of an organization
 */
export async function getTeamMembers(orgId: string): Promise<TeamMember[]> {
  return apiRequest<TeamMember[]>(`/api/organizations/${orgId}/members`);
}

/**
 * Invite a member to an organization
 */
export async function inviteMember(
  orgId: string,
  data: InviteMemberRequest
): Promise<TeamMember> {
  return apiRequest<TeamMember>(`/api/organizations/${orgId}/members`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update a member's role
 */
export async function updateMemberRole(
  orgId: string,
  memberId: string,
  data: UpdateMemberRoleRequest
): Promise<TeamMember> {
  return apiRequest<TeamMember>(
    `/api/organizations/${orgId}/members/${memberId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    }
  );
}

/**
 * Remove a member from an organization
 */
export async function removeMember(
  orgId: string,
  memberId: string
): Promise<void> {
  return apiRequest<void>(`/api/organizations/${orgId}/members/${memberId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Permission API
// ============================================================================

/**
 * Check if user has permission for a resource
 */
export async function checkPermission(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string,
  level: string
): Promise<PermissionCheck> {
  return apiRequest<PermissionCheck>(
    `/api/permissions/check?resource_type=${resourceType}&resource_id=${resourceId}&level=${level}`
  );
}

/**
 * Get all permissions for a resource
 */
export async function getResourcePermissions(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
): Promise<Permission[]> {
  return apiRequest<Permission[]>(
    `/api/permissions?resource_type=${resourceType}&resource_id=${resourceId}`
  );
}

/**
 * Grant permission to a user or team
 */
export async function grantPermission(
  data: GrantPermissionRequest
): Promise<Permission> {
  return apiRequest<Permission>('/api/permissions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Revoke a permission
 */
export async function revokePermission(permissionId: string): Promise<void> {
  return apiRequest<void>(`/api/permissions/${permissionId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Share API
// ============================================================================

/**
 * Get all shares for a resource
 */
export async function getShares(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
): Promise<Share[]> {
  return apiRequest<Share[]>(
    `/api/shares?resource_type=${resourceType}&resource_id=${resourceId}`
  );
}

/**
 * Create a new share
 */
export async function createShare(data: CreateShareRequest): Promise<Share> {
  return apiRequest<Share>('/api/shares', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a share
 */
export async function deleteShare(shareId: string): Promise<void> {
  return apiRequest<void>(`/api/shares/${shareId}`, {
    method: 'DELETE',
  });
}

/**
 * Get all share links for a resource
 */
export async function getShareLinks(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
): Promise<ShareLink[]> {
  return apiRequest<ShareLink[]>(
    `/api/shares/links?resource_type=${resourceType}&resource_id=${resourceId}`
  );
}

/**
 * Create a share link
 */
export async function createShareLink(
  data: CreateShareLinkRequest
): Promise<ShareLink> {
  return apiRequest<ShareLink>('/api/shares/links', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a share link
 */
export async function deleteShareLink(linkId: string): Promise<void> {
  return apiRequest<void>(`/api/shares/links/${linkId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Comment API
// ============================================================================

/**
 * Get all comments for a resource
 */
export async function getComments(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
): Promise<Comment[]> {
  return apiRequest<Comment[]>(
    `/api/comments?resource_type=${resourceType}&resource_id=${resourceId}`
  );
}

/**
 * Get comment threads (grouped by parent)
 */
export async function getCommentThreads(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
): Promise<CommentThread[]> {
  return apiRequest<CommentThread[]>(
    `/api/comments/threads?resource_type=${resourceType}&resource_id=${resourceId}`
  );
}

/**
 * Create a new comment
 */
export async function createComment(
  data: CreateCommentRequest
): Promise<Comment> {
  return apiRequest<Comment>('/api/comments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update a comment
 */
export async function updateComment(
  commentId: string,
  data: UpdateCommentRequest
): Promise<Comment> {
  return apiRequest<Comment>(`/api/comments/${commentId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a comment
 */
export async function deleteComment(commentId: string): Promise<void> {
  return apiRequest<void>(`/api/comments/${commentId}`, {
    method: 'DELETE',
  });
}

/**
 * Resolve a comment
 */
export async function resolveComment(commentId: string): Promise<Comment> {
  return apiRequest<Comment>(`/api/comments/${commentId}/resolve`, {
    method: 'POST',
  });
}

/**
 * Unresolve a comment
 */
export async function unresolveComment(commentId: string): Promise<Comment> {
  return apiRequest<Comment>(`/api/comments/${commentId}/unresolve`, {
    method: 'POST',
  });
}

/**
 * Add a reaction to a comment
 */
export async function addCommentReaction(
  commentId: string,
  emoji: string
): Promise<void> {
  return apiRequest<void>(`/api/comments/${commentId}/reactions`, {
    method: 'POST',
    body: JSON.stringify({ emoji }),
  });
}

/**
 * Remove a reaction from a comment
 */
export async function removeCommentReaction(
  commentId: string,
  reactionId: string
): Promise<void> {
  return apiRequest<void>(
    `/api/comments/${commentId}/reactions/${reactionId}`,
    {
      method: 'DELETE',
    }
  );
}

// ============================================================================
// Version API
// ============================================================================

/**
 * Get all versions for a resource
 */
export async function getVersions(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<Version>> {
  return apiRequest<PaginatedResponse<Version>>(
    `/api/versions?resource_type=${resourceType}&resource_id=${resourceId}&page=${page}&page_size=${pageSize}`
  );
}

/**
 * Get a specific version
 */
export async function getVersion(versionId: string): Promise<Version> {
  return apiRequest<Version>(`/api/versions/${versionId}`);
}

/**
 * Create a new version
 */
export async function createVersion(
  data: CreateVersionRequest
): Promise<Version> {
  return apiRequest<Version>('/api/versions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Restore a version
 */
export async function restoreVersion(versionId: string): Promise<Version> {
  return apiRequest<Version>(`/api/versions/${versionId}/restore`, {
    method: 'POST',
  });
}

/**
 * Compare two versions
 */
export async function compareVersions(
  versionFromId: string,
  versionToId: string
): Promise<VersionDiff> {
  return apiRequest<VersionDiff>(
    `/api/versions/compare?from=${versionFromId}&to=${versionToId}`
  );
}

/**
 * Delete a version
 */
export async function deleteVersion(versionId: string): Promise<void> {
  return apiRequest<void>(`/api/versions/${versionId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Notification API
// ============================================================================

/**
 * Get all notifications for the current user
 */
export async function getNotifications(
  page: number = 1,
  pageSize: number = 20,
  unreadOnly: boolean = false
): Promise<PaginatedResponse<Notification>> {
  return apiRequest<PaginatedResponse<Notification>>(
    `/api/notifications?page=${page}&page_size=${pageSize}&unread_only=${unreadOnly}`
  );
}

/**
 * Get unread notification count
 */
export async function getUnreadNotificationCount(): Promise<number> {
  const response = await apiRequest<{ count: number }>(
    '/api/notifications/unread/count'
  );
  return response.count;
}

/**
 * Mark notifications as read
 */
export async function markNotificationsAsRead(
  data: MarkNotificationReadRequest
): Promise<void> {
  return apiRequest<void>('/api/notifications/read', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsAsRead(): Promise<void> {
  return apiRequest<void>('/api/notifications/read/all', {
    method: 'POST',
  });
}

/**
 * Delete a notification
 */
export async function deleteNotification(notificationId: string): Promise<void> {
  return apiRequest<void>(`/api/notifications/${notificationId}`, {
    method: 'DELETE',
  });
}

/**
 * Get notification preferences
 */
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  return apiRequest<NotificationPreferences>('/api/notifications/preferences');
}

/**
 * Update notification preferences
 */
export async function updateNotificationPreferences(
  preferences: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  return apiRequest<NotificationPreferences>('/api/notifications/preferences', {
    method: 'PATCH',
    body: JSON.stringify(preferences),
  });
}
