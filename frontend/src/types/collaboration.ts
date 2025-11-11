/**
 * Team Collaboration Type Definitions
 *
 * Types for organizations, team members, permissions, sharing,
 * comments, versions, and notifications.
 */

// ============================================================================
// Core Types
// ============================================================================

/**
 * User role in an organization
 */
export enum Role {
  VIEWER = 'viewer',
  EDITOR = 'editor',
  ADMIN = 'admin',
  OWNER = 'owner',
}

/**
 * Permission level for resource access
 */
export enum PermissionLevel {
  VIEW = 'view',
  COMMENT = 'comment',
  EDIT = 'edit',
  ADMIN = 'admin',
}

/**
 * Share link visibility
 */
export enum ShareLinkAccess {
  PRIVATE = 'private',
  ANYONE_WITH_LINK = 'anyone_with_link',
  PUBLIC = 'public',
}

/**
 * Notification type
 */
export enum NotificationType {
  COMMENT = 'comment',
  MENTION = 'mention',
  SHARE = 'share',
  VERSION = 'version',
  MEMBER_ADDED = 'member_added',
  MEMBER_REMOVED = 'member_removed',
  PERMISSION_CHANGED = 'permission_changed',
}

/**
 * Notification delivery channel
 */
export enum NotificationChannel {
  IN_APP = 'in_app',
  EMAIL = 'email',
  BOTH = 'both',
}

// ============================================================================
// Organization Types
// ============================================================================

/**
 * Organization model
 */
export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  member_count?: number;
  video_count?: number;
  settings?: OrganizationSettings;
}

/**
 * Organization settings
 */
export interface OrganizationSettings {
  default_role: Role;
  allow_public_sharing: boolean;
  require_email_verification: boolean;
  max_members?: number;
  retention_days?: number;
}

/**
 * Organization creation request
 */
export interface CreateOrganizationRequest {
  name: string;
  slug?: string;
  description?: string;
  settings?: Partial<OrganizationSettings>;
}

/**
 * Organization update request
 */
export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
  settings?: Partial<OrganizationSettings>;
}

// ============================================================================
// Team Member Types
// ============================================================================

/**
 * Team member model
 */
export interface TeamMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: Role;
  invited_by_id?: string;
  joined_at: string;
  last_active?: string;
  user?: User;
  permissions?: string[];
}

/**
 * Simplified user info for team members
 */
export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
}

/**
 * Team member invitation request
 */
export interface InviteMemberRequest {
  email: string;
  role: Role;
  message?: string;
}

/**
 * Team member role update request
 */
export interface UpdateMemberRoleRequest {
  role: Role;
}

// ============================================================================
// Permission Types
// ============================================================================

/**
 * Permission model for resource access
 */
export interface Permission {
  id: string;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  user_id?: string;
  team_id?: string;
  level: PermissionLevel;
  granted_by_id: string;
  granted_at: string;
  expires_at?: string;
}

/**
 * Permission grant request
 */
export interface GrantPermissionRequest {
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  user_id?: string;
  team_id?: string;
  level: PermissionLevel;
  expires_at?: string;
}

/**
 * Permission check response
 */
export interface PermissionCheck {
  has_permission: boolean;
  level?: PermissionLevel;
  inherited_from?: string;
}

// ============================================================================
// Share Types
// ============================================================================

/**
 * Share model
 */
export interface Share {
  id: string;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  owner_id: string;
  shared_with_user_id?: string;
  shared_with_team_id?: string;
  permission_level: PermissionLevel;
  created_at: string;
  expires_at?: string;
  message?: string;
  shared_with_user?: User;
}

/**
 * Share link model
 */
export interface ShareLink {
  id: string;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  owner_id: string;
  token: string;
  access: ShareLinkAccess;
  permission_level: PermissionLevel;
  password?: string;
  max_uses?: number;
  use_count: number;
  expires_at?: string;
  created_at: string;
}

/**
 * Share creation request
 */
export interface CreateShareRequest {
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  user_id?: string;
  team_id?: string;
  permission_level: PermissionLevel;
  message?: string;
  expires_at?: string;
}

/**
 * Share link creation request
 */
export interface CreateShareLinkRequest {
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  access: ShareLinkAccess;
  permission_level: PermissionLevel;
  password?: string;
  max_uses?: number;
  expires_at?: string;
}

// ============================================================================
// Comment Types
// ============================================================================

/**
 * Comment model
 */
export interface Comment {
  id: string;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  user_id: string;
  parent_id?: string;
  content: string;
  timestamp?: number; // Video timestamp in seconds
  resolved: boolean;
  created_at: string;
  updated_at: string;
  edited: boolean;
  user?: User;
  replies?: Comment[];
  reactions?: CommentReaction[];
}

/**
 * Comment reaction
 */
export interface CommentReaction {
  id: string;
  comment_id: string;
  user_id: string;
  emoji: string;
  created_at: string;
  user?: User;
}

/**
 * Comment creation request
 */
export interface CreateCommentRequest {
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  content: string;
  parent_id?: string;
  timestamp?: number;
}

/**
 * Comment update request
 */
export interface UpdateCommentRequest {
  content: string;
}

/**
 * Comment thread
 */
export interface CommentThread {
  parent: Comment;
  replies: Comment[];
  unread_count?: number;
}

// ============================================================================
// Version Types
// ============================================================================

/**
 * Version model
 */
export interface Version {
  id: string;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  version_number: number;
  created_by_id: string;
  created_at: string;
  description?: string;
  data_snapshot: Record<string, any>;
  metadata?: VersionMetadata;
  created_by?: User;
}

/**
 * Version metadata
 */
export interface VersionMetadata {
  file_size?: number;
  duration?: number;
  changes_summary?: string;
  auto_saved?: boolean;
}

/**
 * Version creation request
 */
export interface CreateVersionRequest {
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  description?: string;
  data_snapshot: Record<string, any>;
  metadata?: VersionMetadata;
}

/**
 * Version comparison diff
 */
export interface VersionDiff {
  version_from: number;
  version_to: number;
  changes: VersionChange[];
  summary: string;
}

/**
 * Individual version change
 */
export interface VersionChange {
  path: string;
  type: 'added' | 'removed' | 'modified';
  old_value?: any;
  new_value?: any;
  description?: string;
}

// ============================================================================
// Notification Types
// ============================================================================

/**
 * Notification model
 */
export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data?: Record<string, any>;
  read: boolean;
  read_at?: string;
  channel: NotificationChannel;
  created_at: string;
  action_url?: string;
}

/**
 * Notification preferences
 */
export interface NotificationPreferences {
  email_enabled: boolean;
  in_app_enabled: boolean;
  notification_types: {
    [key in NotificationType]: boolean;
  };
  digest_frequency?: 'realtime' | 'hourly' | 'daily' | 'weekly';
}

/**
 * Mark notification as read request
 */
export interface MarkNotificationReadRequest {
  notification_ids: string[];
}

// ============================================================================
// WebSocket Types
// ============================================================================

/**
 * WebSocket message types
 */
export enum WSMessageType {
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  JOIN_ROOM = 'join_room',
  LEAVE_ROOM = 'leave_room',
  COMMENT_ADDED = 'comment_added',
  COMMENT_UPDATED = 'comment_updated',
  COMMENT_DELETED = 'comment_deleted',
  USER_TYPING = 'user_typing',
  USER_PRESENCE = 'user_presence',
  NOTIFICATION = 'notification',
}

/**
 * WebSocket message
 */
export interface WSMessage<T = any> {
  type: WSMessageType;
  data: T;
  timestamp: string;
  user_id?: string;
}

/**
 * User presence data
 */
export interface UserPresence {
  user_id: string;
  user: User;
  status: 'online' | 'away' | 'offline';
  last_seen: string;
  current_resource?: {
    type: 'video' | 'project' | 'clip';
    id: string;
  };
}

/**
 * Typing indicator data
 */
export interface TypingIndicator {
  user_id: string;
  user: User;
  resource_type: 'video' | 'project' | 'clip';
  resource_id: string;
  is_typing: boolean;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * API error response
 */
export interface APIError {
  detail: string;
  code?: string;
  field?: string;
}
