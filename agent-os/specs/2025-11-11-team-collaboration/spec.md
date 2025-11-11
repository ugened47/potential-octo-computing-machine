# Specification: Team Collaboration

## Goal
Enable teams to collaborate on video projects with role-based permissions, real-time commenting, sharing capabilities, and version control to support multi-user workflows and improve productivity.

## User Stories
- As a team leader, I want to create an organization and invite team members so that my team can collaborate on video projects
- As an admin, I want to assign roles (viewer, editor, admin) to team members so that I can control who can view, edit, or manage videos
- As an editor, I want to share specific videos with team members or external collaborators so that they can review and provide feedback
- As a viewer, I want to add comments on the timeline so that I can provide feedback on specific moments in the video
- As a user, I want to reply to comments and mention team members so that we can have threaded discussions about video content
- As an editor, I want to see version history of edits so that I can track changes and revert to previous versions if needed
- As an admin, I want to manage team permissions and remove members so that I can maintain security and access control
- As a user, I want to see who else is currently viewing/editing a video so that I can coordinate with teammates in real-time
- As a viewer, I want to receive notifications when I'm mentioned in comments so that I can respond to feedback quickly
- As an admin, I want to see audit logs of all actions taken on videos so that I can track team activity and compliance

## Specific Requirements

### Organization/Team Model & Database

**Organization Model:**
- Create Organization model with:
  - id (UUID, primary key)
  - name (string, required, 2-100 chars)
  - slug (string, unique, URL-friendly identifier)
  - owner_id (UUID, foreign key to User, the creator/owner)
  - plan (enum: 'free', 'pro', 'business', determines features/limits)
  - max_members (integer, based on plan: free=1, pro=3, business=10)
  - settings (JSON, organization preferences)
  - created_at, updated_at timestamps
- Indexes on: slug (unique), owner_id
- Constraints: name must be unique per owner, slug must be globally unique
- Organization settings include: default_permissions, require_approval_for_shares, enable_comments, enable_version_history

**TeamMember Model:**
- Create TeamMember model with:
  - id (UUID, primary key)
  - organization_id (UUID, foreign key to Organization)
  - user_id (UUID, foreign key to User)
  - role (enum: 'viewer', 'editor', 'admin')
  - status (enum: 'invited', 'active', 'suspended')
  - invited_by (UUID, foreign key to User, nullable)
  - invited_at (timestamp, nullable)
  - joined_at (timestamp, nullable)
  - last_active_at (timestamp, nullable)
  - created_at, updated_at timestamps
- Unique constraint: (organization_id, user_id)
- Indexes on: organization_id, user_id, role, status
- Cascade delete when organization or user is deleted

**Role Definitions:**
- **Viewer**: Can view videos, transcripts, highlights; can add comments; cannot edit or delete
- **Editor**: All viewer permissions + can upload, edit, delete videos; can manage own videos' shares
- **Admin**: All editor permissions + can manage organization settings, invite/remove members, manage all videos in organization, view audit logs

**Permission Model:**
- Create VideoPermission model for granular per-video permissions:
  - id (UUID, primary key)
  - video_id (UUID, foreign key to Video)
  - organization_id (UUID, foreign key to Organization, nullable)
  - user_id (UUID, foreign key to User, nullable)
  - permission_level (enum: 'view', 'comment', 'edit', 'admin')
  - granted_by (UUID, foreign key to User)
  - granted_at (timestamp)
  - expires_at (timestamp, nullable, for temporary access)
  - created_at, updated_at timestamps
- Either organization_id or user_id must be set (not both)
- Indexes on: video_id, organization_id, user_id, permission_level
- Composite unique: (video_id, organization_id) or (video_id, user_id)

### Video Sharing System

**VideoShare Model:**
- Create VideoShare model for sharing videos with specific users or teams:
  - id (UUID, primary key)
  - video_id (UUID, foreign key to Video)
  - shared_by (UUID, foreign key to User)
  - shared_with_user_id (UUID, foreign key to User, nullable)
  - shared_with_organization_id (UUID, foreign key to Organization, nullable)
  - permission_level (enum: 'view', 'comment', 'edit')
  - access_type (enum: 'direct', 'link', 'organization')
  - share_token (string, unique, for link-based sharing)
  - expires_at (timestamp, nullable)
  - is_active (boolean, default true)
  - access_count (integer, tracks how many times accessed)
  - last_accessed_at (timestamp, nullable)
  - message (text, optional message from sharer)
  - created_at, updated_at timestamps
- Either shared_with_user_id or shared_with_organization_id must be set
- Indexes on: video_id, shared_by, shared_with_user_id, shared_with_organization_id, share_token (unique), expires_at
- share_token generated with cryptographically secure random string (32 chars)

**Share Access Types:**
- **Direct**: Shared with specific user, requires authentication
- **Link**: Anyone with link can access (share_token), optional password protection
- **Organization**: Shared with entire organization, all members can access

**Share Notifications:**
- Create Notification model for share notifications:
  - id (UUID, primary key)
  - user_id (UUID, foreign key to User)
  - type (enum: 'share', 'comment', 'mention', 'version')
  - related_entity_type (string: 'video_share', 'comment', 'version')
  - related_entity_id (UUID)
  - title (string)
  - message (text)
  - is_read (boolean, default false)
  - read_at (timestamp, nullable)
  - action_url (string, link to relevant page)
  - created_at timestamp
- Indexes on: user_id, is_read, created_at DESC

### Comment System

**Comment Model:**
- Create Comment model for timeline comments:
  - id (UUID, primary key)
  - video_id (UUID, foreign key to Video)
  - user_id (UUID, foreign key to User)
  - parent_comment_id (UUID, foreign key to Comment, nullable, for replies)
  - timestamp (float, video timestamp in seconds where comment applies)
  - timestamp_end (float, nullable, for range comments)
  - content (text, required, 1-10000 chars)
  - mentions (UUID array, user IDs mentioned in comment)
  - attachments (JSON array, optional file attachments)
  - is_resolved (boolean, default false)
  - resolved_by (UUID, foreign key to User, nullable)
  - resolved_at (timestamp, nullable)
  - is_edited (boolean, default false)
  - edited_at (timestamp, nullable)
  - created_at, updated_at timestamps
- Indexes on: video_id, user_id, parent_comment_id, timestamp, is_resolved, created_at DESC
- Support for nested replies (max 3 levels deep)
- Soft delete support (is_deleted flag)

**Comment Reactions:**
- Create CommentReaction model:
  - id (UUID, primary key)
  - comment_id (UUID, foreign key to Comment)
  - user_id (UUID, foreign key to User)
  - reaction_type (enum: 'like', 'love', 'laugh', 'confused', 'eyes')
  - created_at timestamp
- Unique constraint: (comment_id, user_id)
- Indexes on: comment_id, user_id

**Comment Mentions:**
- Parse comment content for @mentions (e.g., "@username")
- Validate mentioned users have access to the video
- Store mentioned user IDs in mentions array
- Create notifications for mentioned users
- Highlight mentions in comment UI

### Version Control System

**Version Model:**
- Create Version model for tracking video edit history:
  - id (UUID, primary key)
  - video_id (UUID, foreign key to Video)
  - version_number (integer, auto-increment per video, starts at 1)
  - created_by (UUID, foreign key to User)
  - change_type (enum: 'upload', 'edit', 'export', 'silence_removal', 'clip', 'subtitle', 'rollback')
  - change_summary (string, brief description)
  - change_details (JSON, detailed changes)
  - video_metadata_snapshot (JSON, video state at this version)
  - file_url (string, S3 URL if applicable)
  - file_size (bigint, bytes)
  - duration (float, seconds)
  - transcript_snapshot (JSON, transcript state if changed)
  - timeline_snapshot (JSON, timeline state if changed)
  - parent_version_id (UUID, foreign key to Version, nullable, for rollbacks)
  - is_current (boolean, only one version per video is current)
  - created_at timestamp
- Unique constraint: (video_id, version_number)
- Indexes on: video_id, version_number DESC, is_current, created_at DESC
- Cascade delete when video is deleted

**Version Change Details:**
- change_details structure (JSON):
  ```json
  {
    "action": "silence_removal",
    "segments_removed": 15,
    "time_saved": 120.5,
    "settings": {"threshold": -40, "min_duration": 1.0},
    "before_duration": 1800,
    "after_duration": 1679.5
  }
  ```
- Capture meaningful metadata for each change type
- Store enough information to display diff or summary

**Version Limits:**
- Retain last 30 versions per video (configurable per plan)
- Older versions archived or deleted (file kept in S3 Glacier if configured)
- Total version storage counts against plan storage limit

**Version Rollback:**
- Allow rollback to previous version
- Create new version with parent_version_id pointing to rolled-back version
- Restore video file, transcript, timeline from snapshot
- Mark new version as current

### Role-Based Access Control (RBAC)

**Permission Checking Service:**
- Create PermissionService with methods:
  - can_view_video(user_id, video_id): Check if user can view video
  - can_edit_video(user_id, video_id): Check if user can edit video
  - can_delete_video(user_id, video_id): Check if user can delete video
  - can_comment_on_video(user_id, video_id): Check if user can comment
  - can_share_video(user_id, video_id): Check if user can share
  - can_manage_organization(user_id, org_id): Check if user is admin
  - get_user_role(user_id, org_id): Get user's role in organization
  - get_video_permissions(user_id, video_id): Get all permissions for video
- Permission hierarchy: admin > editor > viewer
- Check multiple sources: ownership, organization membership, direct shares, link access
- Cache permission checks in Redis (TTL: 5 minutes)

**Permission Resolution Logic:**
1. Check if user is video owner (full access)
2. Check if user is organization admin (full access to org videos)
3. Check if video shared with user's organization (use org member's role)
4. Check if video directly shared with user (use share permission level)
5. Check if user has link access via share_token
6. Default: deny access

**Middleware/Decorator:**
- Create FastAPI dependency for permission checking:
  - require_permission(permission: str) decorator
  - Check permissions before endpoint execution
  - Return 403 Forbidden if insufficient permissions
  - Example: @require_permission('edit') on edit endpoints

### Backend API Endpoints

**Organization Management:**
- POST /api/organizations: Create new organization
  - Body: {name, slug (optional, auto-generated), plan}
  - Returns: Organization object
  - User becomes owner and admin automatically
- GET /api/organizations: List user's organizations
  - Returns: Array of organizations user belongs to
- GET /api/organizations/{id}: Get organization details
  - Returns: Organization object with member count, settings
- PATCH /api/organizations/{id}: Update organization
  - Body: {name, settings}
  - Requires: admin role
  - Returns: Updated organization
- DELETE /api/organizations/{id}: Delete organization
  - Requires: owner only
  - Soft delete (archive) or hard delete with confirmation
  - Cascades to team members, permissions, shares

**Team Member Management:**
- POST /api/organizations/{id}/members: Invite team member
  - Body: {email, role}
  - Requires: admin role
  - Sends invitation email, creates pending TeamMember
  - Returns: TeamMember object
- GET /api/organizations/{id}/members: List team members
  - Query params: status, role
  - Returns: Array of team members with user info
- GET /api/organizations/{id}/members/{member_id}: Get member details
  - Returns: TeamMember object with activity stats
- PATCH /api/organizations/{id}/members/{member_id}: Update member
  - Body: {role, status}
  - Requires: admin role
  - Returns: Updated TeamMember
- DELETE /api/organizations/{id}/members/{member_id}: Remove member
  - Requires: admin role
  - Revokes all permissions, notifies user
- POST /api/organizations/{id}/accept-invitation: Accept invitation
  - Body: {invitation_token}
  - Updates status to active, sets joined_at
  - Returns: TeamMember object

**Video Sharing:**
- POST /api/videos/{id}/share: Share video
  - Body: {shared_with_user_id (optional), shared_with_organization_id (optional), permission_level, access_type, expires_at (optional), message (optional), require_password (boolean)}
  - Returns: VideoShare object with share_token if link access
  - Creates notifications for recipients
- GET /api/videos/{id}/shares: List video shares
  - Returns: Array of shares with recipient info
- GET /api/shares/{share_id}: Get share details
  - Returns: VideoShare object
- PATCH /api/shares/{share_id}: Update share
  - Body: {permission_level, expires_at, is_active}
  - Returns: Updated share
- DELETE /api/shares/{share_id}: Revoke share
  - Marks as inactive, notifies recipients
- GET /api/shares/token/{share_token}: Access video via share link
  - Optional: ?password=xxx for password-protected shares
  - Returns: Video info and temporary access token
  - Increments access_count

**Comment System:**
- POST /api/videos/{id}/comments: Create comment
  - Body: {timestamp, timestamp_end (optional), content, parent_comment_id (optional)}
  - Requires: comment permission
  - Parses mentions, creates notifications
  - Returns: Comment object
  - Broadcasts via WebSocket to active users
- GET /api/videos/{id}/comments: List comments
  - Query params: timestamp_range, is_resolved, user_id, limit, offset
  - Returns: Array of comments with nested replies
  - Include user info, reaction counts
- GET /api/comments/{id}: Get comment details
  - Returns: Comment object with full thread
- PATCH /api/comments/{id}: Update comment
  - Body: {content, is_resolved}
  - Only author or admin can edit
  - Sets is_edited flag
  - Returns: Updated comment
- DELETE /api/comments/{id}: Delete comment
  - Soft delete, preserves thread structure
  - Only author or admin can delete
- POST /api/comments/{id}/reactions: Add reaction
  - Body: {reaction_type}
  - Toggle reaction (remove if already exists)
  - Returns: Updated reaction counts

**Version History:**
- GET /api/videos/{id}/versions: List versions
  - Query params: limit, offset
  - Returns: Array of versions with change summaries
- GET /api/versions/{id}: Get version details
  - Returns: Version object with full metadata
- POST /api/videos/{id}/versions/rollback: Rollback to version
  - Body: {version_id}
  - Requires: edit permission
  - Creates new version, restores state
  - Returns: New current version
- GET /api/versions/{id}/diff: Compare versions
  - Query param: compare_to (version_id)
  - Returns: Detailed diff of changes
- GET /api/versions/{id}/download: Download version file
  - Returns: S3 presigned URL for version file

**Notifications:**
- GET /api/notifications: List user notifications
  - Query params: type, is_read, limit, offset
  - Returns: Array of notifications
- PATCH /api/notifications/{id}/read: Mark as read
  - Returns: Updated notification
- POST /api/notifications/mark-all-read: Mark all as read
  - Returns: Count of marked notifications
- DELETE /api/notifications/{id}: Delete notification

**Audit Logs:**
- GET /api/organizations/{id}/audit-logs: List audit logs
  - Requires: admin role
  - Query params: user_id, action_type, date_range, limit, offset
  - Returns: Array of audit log entries
- Audit log captures: user, action, resource, timestamp, IP, user agent
- Actions logged: member_added, member_removed, role_changed, video_shared, video_deleted, settings_changed

**Real-time Presence:**
- GET /api/videos/{id}/presence: Get active users
  - Returns: Array of users currently viewing/editing video
- POST /api/videos/{id}/presence: Update presence (via WebSocket or polling)
  - Body: {status: 'viewing' | 'editing' | 'idle'}
  - TTL: 30 seconds (heartbeat required)

### Frontend Components

**OrganizationManager Component:**
- Client component for managing organizations
- Props: None (fetches current user's organizations)
- Features:
  - List all organizations user belongs to
  - Create new organization form (name, plan selection)
  - Switch between organizations (context/state management)
  - View organization details (members, settings, usage stats)
  - Delete organization (owner only, with confirmation)
- Layout: Card grid or list with organization name, plan, member count
- Actions per org: View, Settings, Switch, Leave/Delete
- Shadcn components: Card, Button, Dialog, Select, Form
- Create file: `frontend/src/components/team/OrganizationManager.tsx`

**TeamMembersPanel Component:**
- Client component for managing team members
- Props: organizationId (string)
- Features:
  - List all team members with roles and status
  - Invite new member (email input, role selection)
  - Update member role (dropdown, admin only)
  - Remove member (confirmation dialog, admin only)
  - Resend invitation (for pending invites)
  - Search/filter members by role, status
  - Show member activity (last active, videos created)
- Table layout: Avatar, Name, Email, Role, Status, Last Active, Actions
- Role badges with color coding: Admin (red), Editor (blue), Viewer (gray)
- Empty state: "No team members yet. Invite your first member!"
- Shadcn components: Table, Badge, Button, Select, Dialog, Input
- Create file: `frontend/src/components/team/TeamMembersPanel.tsx`

**ShareModal Component:**
- Client component for sharing videos
- Props: videoId (string), onShare (function, optional)
- Features:
  - Share with specific user (search/select)
  - Share with organization (dropdown)
  - Generate share link (with copy button)
  - Set permission level (view, comment, edit)
  - Set expiration date (date picker)
  - Add message to share
  - Password protect link (checkbox, password input)
  - List existing shares (recipients, permissions, actions)
  - Revoke share (delete button with confirmation)
- Tabs: "Share with User", "Share with Team", "Share Link", "Active Shares"
- Share link section: Display link, copy button, QR code (optional)
- Active shares table: Recipient, Permission, Created, Expires, Actions (Edit, Revoke)
- Shadcn components: Dialog, Tabs, Input, Select, DatePicker, Button, Table
- Create file: `frontend/src/components/team/ShareModal.tsx`

**CommentsPanel Component:**
- Client component for displaying and managing comments
- Props: videoId (string), currentTime (number), onSeek (function)
- Features:
  - List all comments sorted by timestamp
  - Filter: All comments, Unresolved, My comments
  - Comment card shows: User avatar, name, timestamp, content, time ago
  - Click timestamp to seek video to that point
  - Reply to comment (nested thread, max 3 levels)
  - Edit own comment (inline editing)
  - Delete own comment (soft delete)
  - Resolve comment (checkbox, marks as done)
  - React to comment (emoji reactions: like, love, etc.)
  - Mention users with @autocomplete
  - Highlight current time's comments
- Real-time updates: New comments appear instantly (WebSocket)
- Optimistic updates: Show own comments immediately
- Empty state: "No comments yet. Be the first to comment!"
- Shadcn components: Card, Button, Textarea, Badge, Avatar, Popover
- Create file: `frontend/src/components/team/CommentsPanel.tsx`

**CommentThread Component:**
- Client component for displaying comment with replies
- Props: comment (Comment), onReply (function), onEdit (function), onDelete (function), onResolve (function), onReact (function)
- Features:
  - Display comment content with formatted text
  - Show edit indicator if edited
  - Show resolved status with checkmark
  - Display reactions with counts
  - Reply button expands reply form
  - Nested replies indented
  - Mention highlighting (@username in blue)
  - Timestamp link to video position
- Actions dropdown: Edit, Delete, Resolve (context-aware based on permissions)
- Shadcn components: Card, Button, Textarea, Badge, Avatar, DropdownMenu
- Create file: `frontend/src/components/team/CommentThread.tsx`

**CommentForm Component:**
- Client component for creating/editing comments
- Props: videoId (string), timestamp (number), parentCommentId (string, optional), editComment (Comment, optional), onSubmit (function), onCancel (function)
- Features:
  - Textarea for comment content (auto-resize)
  - Mention autocomplete (@username)
  - Timestamp display (shows video position)
  - Timestamp range selection (optional, for range comments)
  - Attach file (optional, for screenshots or related files)
  - Character count (max 10000)
  - Submit button (disabled if empty)
  - Cancel button (for edits or replies)
- Keyboard shortcuts: Ctrl+Enter to submit, Esc to cancel
- Validation: Require content, validate timestamp
- Shadcn components: Textarea, Button, Popover (for mentions)
- Create file: `frontend/src/components/team/CommentForm.tsx`

**VersionHistory Component:**
- Client component for displaying version history
- Props: videoId (string), onRestore (function, optional)
- Features:
  - List all versions in reverse chronological order
  - Version card shows: Version number, created by, time ago, change type, summary
  - Change details expandable (show full change_details JSON)
  - Visual timeline connecting versions
  - Current version highlighted (green badge)
  - View version details button
  - Compare versions button (select two versions)
  - Restore version button (creates rollback, admin/editor only)
  - Download version file (if available)
- Version types with icons: Upload (cloud), Edit (pencil), Export (download), Silence removal (volume), Clip (scissors)
- Confirmation dialog for restore action
- Empty state: "No version history yet."
- Shadcn components: Card, Button, Badge, ScrollArea, Dialog
- Create file: `frontend/src/components/team/VersionHistory.tsx`

**VersionDiff Component:**
- Client component for comparing two versions
- Props: videoId (string), version1 (Version), version2 (Version)
- Features:
  - Side-by-side comparison layout
  - Highlight differences in metadata
  - Show duration change, file size change
  - Display change summaries for each version
  - Timeline diff (if timeline changed)
  - Transcript diff (if transcript changed)
  - Visual indicators: Added (green), Removed (red), Modified (yellow)
- Tabs: Overview, Timeline, Transcript, Metadata
- Shadcn components: Card, Badge, Tabs, Table
- Create file: `frontend/src/components/team/VersionDiff.tsx`

**ActiveUsers Component:**
- Client component showing active users on video
- Props: videoId (string)
- Features:
  - Display avatars of users currently viewing/editing
  - Real-time presence updates (WebSocket)
  - User status indicators: Viewing (eye icon), Editing (pencil icon), Idle (moon icon)
  - Hover shows user name and status
  - Show count if more than 5 users ("+3 more")
  - Auto-update presence (heartbeat every 30s)
- Layout: Horizontal avatar stack with overlap
- Shadcn components: Avatar, Tooltip
- Create file: `frontend/src/components/team/ActiveUsers.tsx`

**NotificationBell Component:**
- Client component for notification center
- Props: None (fetches current user's notifications)
- Features:
  - Bell icon with unread count badge
  - Dropdown panel with notification list
  - Notification items: Icon, title, message, time ago
  - Mark as read on click
  - Mark all as read button
  - View all notifications link (to full page)
  - Real-time updates (WebSocket for new notifications)
  - Group by date: Today, Yesterday, This Week, Older
  - Empty state: "No new notifications"
- Notification types with icons: Share (users), Comment (message), Mention (at), Version (clock)
- Click notification navigates to relevant page
- Shadcn components: Popover, Button, Badge, ScrollArea
- Create file: `frontend/src/components/team/NotificationBell.tsx`

**PermissionGuard Component:**
- Client component wrapper for permission-based rendering
- Props: requiredPermission (string), videoId (string, optional), organizationId (string, optional), fallback (ReactNode, optional), children (ReactNode)
- Features:
  - Check if current user has required permission
  - Render children if permission granted
  - Render fallback if permission denied
  - Show loading state while checking permissions
  - Cache permission results (React Context)
- Example usage:
  ```tsx
  <PermissionGuard requiredPermission="edit" videoId={id}>
    <EditButton />
  </PermissionGuard>
  ```
- Create file: `frontend/src/components/team/PermissionGuard.tsx`

### Frontend State Management

**Team Context/Store:**
- Create TeamContext for organization and member state
- State: currentOrganization, organizations, teamMembers, userRole
- Actions: setCurrentOrganization, fetchOrganizations, fetchTeamMembers, inviteMember, updateMember, removeMember
- Use React Context API or Zustand for state management
- Persist currentOrganization in localStorage
- Create file: `frontend/src/contexts/TeamContext.tsx`

**Permissions Context:**
- Create PermissionsContext for caching permission checks
- State: videoPermissions (Map<videoId, permissions>), organizationRoles (Map<orgId, role>)
- Actions: checkPermission, refreshPermissions, clearCache
- Cache results for performance (5 minute TTL)
- Create file: `frontend/src/contexts/PermissionsContext.tsx`

**Comments Context:**
- Create CommentsContext for comment state and real-time updates
- State: comments (array), activeFilters, unreadCount
- Actions: addComment, updateComment, deleteComment, resolveComment, addReaction
- WebSocket integration for real-time comment updates
- Optimistic updates for better UX
- Create file: `frontend/src/contexts/CommentsContext.tsx`

### Frontend API Client Functions

**Organization API:**
- createOrganization(data): Create organization, returns Promise<Organization>
- getOrganizations(): Get user's organizations, returns Promise<Organization[]>
- getOrganization(id): Get organization details, returns Promise<Organization>
- updateOrganization(id, data): Update organization, returns Promise<Organization>
- deleteOrganization(id): Delete organization, returns Promise<void>

**Team Member API:**
- inviteTeamMember(orgId, data): Invite member, returns Promise<TeamMember>
- getTeamMembers(orgId, params): Get members, returns Promise<TeamMember[]>
- getTeamMember(orgId, memberId): Get member details, returns Promise<TeamMember>
- updateTeamMember(orgId, memberId, data): Update member, returns Promise<TeamMember>
- removeTeamMember(orgId, memberId): Remove member, returns Promise<void>
- acceptInvitation(token): Accept invitation, returns Promise<TeamMember>

**Video Sharing API:**
- shareVideo(videoId, data): Share video, returns Promise<VideoShare>
- getVideoShares(videoId): Get shares, returns Promise<VideoShare[]>
- getShare(shareId): Get share details, returns Promise<VideoShare>
- updateShare(shareId, data): Update share, returns Promise<VideoShare>
- revokeShare(shareId): Revoke share, returns Promise<void>
- accessSharedVideo(token, password): Access via link, returns Promise<{video: Video, access_token: string}>

**Comments API:**
- createComment(videoId, data): Create comment, returns Promise<Comment>
- getComments(videoId, params): Get comments, returns Promise<Comment[]>
- getComment(id): Get comment details, returns Promise<Comment>
- updateComment(id, data): Update comment, returns Promise<Comment>
- deleteComment(id): Delete comment, returns Promise<void>
- addReaction(commentId, type): Add/remove reaction, returns Promise<ReactionCounts>

**Version History API:**
- getVersions(videoId, params): Get versions, returns Promise<Version[]>
- getVersion(id): Get version details, returns Promise<Version>
- rollbackToVersion(videoId, versionId): Rollback, returns Promise<Version>
- compareVersions(versionId, compareToId): Compare versions, returns Promise<VersionDiff>
- downloadVersion(id): Get download URL, returns Promise<{url: string}>

**Notifications API:**
- getNotifications(params): Get notifications, returns Promise<Notification[]>
- markNotificationRead(id): Mark as read, returns Promise<Notification>
- markAllNotificationsRead(): Mark all as read, returns Promise<{count: number}>
- deleteNotification(id): Delete notification, returns Promise<void>

**Permissions API:**
- checkVideoPermission(videoId, permission): Check permission, returns Promise<{allowed: boolean}>
- getUserRole(orgId): Get user role, returns Promise<{role: string}>
- getVideoPermissions(videoId): Get all permissions, returns Promise<VideoPermission[]>

**Presence API:**
- getActiveUsers(videoId): Get active users, returns Promise<PresenceUser[]>
- updatePresence(videoId, status): Update user presence, returns Promise<void>

### TypeScript Type Definitions

**Organization Types:**
```typescript
interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  plan: 'free' | 'pro' | 'business';
  max_members: number;
  settings: OrganizationSettings;
  created_at: string;
  updated_at: string;
}

interface OrganizationSettings {
  default_permissions: PermissionLevel;
  require_approval_for_shares: boolean;
  enable_comments: boolean;
  enable_version_history: boolean;
}

interface TeamMember {
  id: string;
  organization_id: string;
  user_id: string;
  user: User;
  role: 'viewer' | 'editor' | 'admin';
  status: 'invited' | 'active' | 'suspended';
  invited_by?: string;
  invited_at?: string;
  joined_at?: string;
  last_active_at?: string;
  created_at: string;
  updated_at: string;
}
```

**Permission Types:**
```typescript
type PermissionLevel = 'view' | 'comment' | 'edit' | 'admin';

interface VideoPermission {
  id: string;
  video_id: string;
  organization_id?: string;
  user_id?: string;
  permission_level: PermissionLevel;
  granted_by: string;
  granted_at: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

interface PermissionCheck {
  allowed: boolean;
  reason?: string;
  required_role?: string;
}
```

**Sharing Types:**
```typescript
interface VideoShare {
  id: string;
  video_id: string;
  shared_by: string;
  shared_with_user_id?: string;
  shared_with_user?: User;
  shared_with_organization_id?: string;
  shared_with_organization?: Organization;
  permission_level: PermissionLevel;
  access_type: 'direct' | 'link' | 'organization';
  share_token?: string;
  expires_at?: string;
  is_active: boolean;
  access_count: number;
  last_accessed_at?: string;
  message?: string;
  created_at: string;
  updated_at: string;
}

interface ShareVideoRequest {
  shared_with_user_id?: string;
  shared_with_organization_id?: string;
  permission_level: PermissionLevel;
  access_type: 'direct' | 'link' | 'organization';
  expires_at?: string;
  message?: string;
  require_password?: boolean;
  password?: string;
}
```

**Comment Types:**
```typescript
interface Comment {
  id: string;
  video_id: string;
  user_id: string;
  user: User;
  parent_comment_id?: string;
  replies?: Comment[];
  timestamp: number;
  timestamp_end?: number;
  content: string;
  mentions: string[];
  mentioned_users?: User[];
  attachments?: CommentAttachment[];
  is_resolved: boolean;
  resolved_by?: string;
  resolved_at?: string;
  is_edited: boolean;
  edited_at?: string;
  reactions: ReactionCounts;
  created_at: string;
  updated_at: string;
}

interface CommentAttachment {
  id: string;
  filename: string;
  url: string;
  mime_type: string;
  size: number;
}

interface ReactionCounts {
  like: number;
  love: number;
  laugh: number;
  confused: number;
  eyes: number;
  user_reaction?: ReactionType;
}

type ReactionType = 'like' | 'love' | 'laugh' | 'confused' | 'eyes';

interface CreateCommentRequest {
  timestamp: number;
  timestamp_end?: number;
  content: string;
  parent_comment_id?: string;
}
```

**Version Types:**
```typescript
interface Version {
  id: string;
  video_id: string;
  version_number: number;
  created_by: string;
  creator: User;
  change_type: ChangeType;
  change_summary: string;
  change_details: ChangeDetails;
  video_metadata_snapshot: VideoMetadata;
  file_url?: string;
  file_size?: number;
  duration?: number;
  transcript_snapshot?: any;
  timeline_snapshot?: any;
  parent_version_id?: string;
  is_current: boolean;
  created_at: string;
}

type ChangeType = 'upload' | 'edit' | 'export' | 'silence_removal' | 'clip' | 'subtitle' | 'rollback';

interface ChangeDetails {
  action: string;
  [key: string]: any; // Flexible structure based on change_type
}

interface VersionDiff {
  version1: Version;
  version2: Version;
  metadata_changes: MetadataChange[];
  timeline_changes?: TimelineChange[];
  transcript_changes?: TranscriptChange[];
}

interface MetadataChange {
  field: string;
  old_value: any;
  new_value: any;
  change_type: 'added' | 'removed' | 'modified';
}
```

**Notification Types:**
```typescript
interface Notification {
  id: string;
  user_id: string;
  type: 'share' | 'comment' | 'mention' | 'version';
  related_entity_type: string;
  related_entity_id: string;
  title: string;
  message: string;
  is_read: boolean;
  read_at?: string;
  action_url: string;
  created_at: string;
}
```

**Presence Types:**
```typescript
interface PresenceUser {
  user_id: string;
  user: User;
  status: 'viewing' | 'editing' | 'idle';
  last_seen: string;
}

interface PresenceUpdate {
  status: 'viewing' | 'editing' | 'idle';
}
```

### Real-time Collaboration (WebSocket)

**WebSocket Server:**
- Set up WebSocket server using FastAPI WebSocket support
- Endpoint: ws://api/ws/videos/{video_id}
- Authentication: JWT token via query param or initial message
- Connection management: Track connections per video
- Heartbeat: Ping/pong every 30s to keep connection alive
- Reconnection: Client auto-reconnect with exponential backoff

**WebSocket Message Types:**
```typescript
// Client -> Server
type ClientMessage =
  | { type: 'subscribe', video_id: string }
  | { type: 'unsubscribe', video_id: string }
  | { type: 'presence_update', status: 'viewing' | 'editing' | 'idle' }
  | { type: 'comment_typing', is_typing: boolean }
  | { type: 'ping' }

// Server -> Client
type ServerMessage =
  | { type: 'comment_created', comment: Comment }
  | { type: 'comment_updated', comment: Comment }
  | { type: 'comment_deleted', comment_id: string }
  | { type: 'presence_update', users: PresenceUser[] }
  | { type: 'video_updated', video: Video }
  | { type: 'notification', notification: Notification }
  | { type: 'pong' }
```

**Frontend WebSocket Client:**
- Create useWebSocket hook for managing WebSocket connections
- Auto-connect when viewing video
- Handle reconnection with exponential backoff
- Update local state on server messages (comments, presence, etc.)
- Send presence updates every 30s
- Cleanup on unmount
- Create file: `frontend/src/hooks/useWebSocket.ts`

**Broadcasting Service:**
- Backend service for broadcasting messages to connected clients
- broadcast_to_video(video_id, message): Send to all users viewing video
- broadcast_to_user(user_id, message): Send to specific user (all connections)
- broadcast_to_organization(org_id, message): Send to all org members
- Use Redis pub/sub for multi-server coordination

### Testing Requirements

**Backend Tests:**
- Unit tests for permission checking logic (PermissionService)
- Unit tests for RBAC resolution (multiple permission sources)
- Integration tests for all API endpoints (organizations, members, shares, comments, versions)
- Test permission enforcement on endpoints (403 responses)
- Test share link access (with/without password, expiration)
- Test comment mentions and notifications
- Test version creation and rollback
- Test WebSocket connection and message broadcasting
- Test concurrent access and race conditions
- Coverage target: >85%

**Frontend Tests:**
- Component tests for all team collaboration components
- Test permission-based rendering (PermissionGuard)
- Test share modal functionality (create, list, revoke shares)
- Test comment creation with mentions
- Test comment real-time updates (mock WebSocket)
- Test version history display and rollback
- Test notification display and mark as read
- Test active users presence updates
- Coverage target: >80%

**E2E Tests:**
- Full collaboration workflow:
  1. Create organization
  2. Invite team member
  3. Share video with team
  4. Add comments with mentions
  5. Reply to comments
  6. Resolve comments
  7. View version history
  8. Rollback to previous version
- Test different roles (viewer, editor, admin)
- Test permission enforcement (viewer cannot edit)
- Test share link access (anonymous user)
- Test real-time comment updates (multiple browser sessions)
- Test notifications delivery and actions

**Load Tests:**
- Test WebSocket scalability (100+ concurrent connections per video)
- Test comment creation performance (10+ users commenting simultaneously)
- Test permission checking performance (1000+ checks/second)
- Test version history with 100+ versions

**Security Tests:**
- Test unauthorized access attempts (403 responses)
- Test SQL injection in comment content
- Test XSS in comment mentions
- Test CSRF protection on state-changing operations
- Test share token brute-force protection
- Test rate limiting on invitations, shares, comments

### Security Considerations

**Authentication & Authorization:**
- Verify JWT token on all endpoints
- Check permissions before any operation
- Validate user belongs to organization before granting access
- Prevent privilege escalation (viewer trying to become admin)
- Audit all permission changes

**Data Validation:**
- Validate all inputs (organization names, comment content, etc.)
- Sanitize comment content (prevent XSS)
- Validate user IDs in mentions (must have video access)
- Validate share expiration dates (reasonable future dates)
- Rate limit: Invitations (10/hour), Shares (20/hour), Comments (60/hour)

**Share Link Security:**
- Generate cryptographically secure random tokens (32+ chars)
- Optional password protection (bcrypt hashed)
- Enforce expiration dates (auto-revoke expired shares)
- Track access count and last accessed (detect abuse)
- Rate limit share link access (100 access/hour per token)
- Option to revoke all share links for a video

**Comment Security:**
- Validate comment length (max 10000 chars)
- Sanitize HTML/scripts in comment content
- Prevent mention spam (max 10 mentions per comment)
- Rate limit comment creation (60 per hour per user)
- Soft delete to preserve thread integrity
- Admin can delete any comment (moderation)

**Version Control Security:**
- Limit version retention (30 per video)
- Require edit permission for rollback
- Prevent rollback loops (track parent_version_id)
- Version files in S3 with restricted access (presigned URLs only)

**WebSocket Security:**
- Authenticate WebSocket connections (JWT token)
- Validate message types and payloads
- Rate limit messages (100/minute per connection)
- Prevent cross-video message injection
- Auto-disconnect idle connections (10 minutes)

**Privacy:**
- Users can only see organizations they belong to
- Comments only visible to users with video access
- Audit logs only visible to admins
- Notifications contain minimal sensitive data
- GDPR: Export all user data, delete account cascades properly

### Performance Considerations

**Database Optimization:**
- Indexes on all foreign keys and frequently queried fields
- Composite indexes for common queries (video_id + timestamp for comments)
- Use database connection pooling (AsyncPG)
- Paginate large result sets (comments, versions, audit logs)
- Aggregate queries for counts (avoid N+1 queries)

**Caching Strategy:**
- Cache permission checks in Redis (5 minute TTL)
- Cache organization membership (5 minute TTL)
- Cache active users list (30 second TTL)
- Cache video share configuration (1 minute TTL)
- Invalidate cache on permission changes

**WebSocket Optimization:**
- Limit concurrent connections per user (5 max)
- Batch presence updates (send every 5 seconds)
- Compress large messages (JSON compression)
- Use Redis pub/sub for horizontal scaling
- Load balance WebSocket connections

**Frontend Optimization:**
- Lazy load comment threads (load replies on demand)
- Virtual scrolling for long comment lists
- Debounce mention autocomplete (300ms)
- Optimistic updates for comments (immediate UI feedback)
- Cache organization/member data in Context
- Use SWR or React Query for data fetching with caching

**Notification Optimization:**
- Batch notifications (don't send for every single action)
- Debounce mention notifications (1 per comment, not per character)
- Use WebSocket for real-time delivery (avoid polling)
- Store only last 100 notifications per user (archive older)

### Integration Points

**Video Editor Integration:**
- Add "Comments" panel to video editor layout
- Display comment markers on timeline at timestamp positions
- Click comment marker to highlight comment and seek video
- Add "Share" button to video editor toolbar
- Show "Active Users" avatars in editor header
- Add "Version" indicator showing current version number

**Dashboard Integration:**
- Show "Shared with me" section in video list
- Display share icon and count on video cards
- Show organization badge on organization-owned videos
- Filter videos by: My Videos, Shared with Me, Organization Videos
- Bulk share action for multiple videos

**Notification Integration:**
- Add NotificationBell to main app header
- Show unread count badge
- Real-time notification delivery via WebSocket
- Email notifications for important events (share, mention, invitation)
- Notification preferences page (which events to notify)

**User Profile Integration:**
- Show organizations user belongs to
- List team memberships and roles
- Activity feed (recent comments, shares, version created)
- Manage notification preferences

### Deployment Considerations

**Database Migration:**
- Run Alembic migrations in order:
  1. Create Organization model
  2. Create TeamMember model
  3. Create VideoPermission model
  4. Create VideoShare model
  5. Create Comment model
  6. Create CommentReaction model
  7. Create Version model
  8. Create Notification model
  9. Add indexes
- Ensure no breaking changes to existing Video model
- Migrate existing videos to default "personal" organization (optional)

**Feature Flags:**
- Enable team collaboration features gradually
- Flag: enable_organizations (default: false)
- Flag: enable_comments (default: true)
- Flag: enable_version_history (default: true)
- Flag: enable_websocket (default: true)
- Allow per-plan feature gating (free vs pro vs business)

**Monitoring:**
- Track WebSocket connection count, errors, disconnects
- Track comment creation rate, spam attempts
- Track permission check latency
- Track share link usage, access count
- Alert on: WebSocket errors, high permission check latency, comment spam

**Rollout Plan:**
1. Deploy backend API (disabled via feature flags)
2. Run database migrations
3. Deploy frontend (hidden behind feature flag)
4. Enable for internal testing (select users)
5. Beta test with 50 users for 2 weeks
6. Collect feedback, fix bugs
7. Full rollout to all users (enable feature flags)

## Success Criteria

**Functionality:**
- Users can create organizations and invite team members
- Users can share videos with specific users, teams, or via link
- Users can add comments on timeline with mentions and replies
- Users can view version history and rollback to previous versions
- Permission system correctly enforces role-based access (viewer, editor, admin)
- Real-time updates work (comments, presence, notifications appear instantly)
- Notifications delivered for shares, mentions, comments
- Audit logs capture all organization/team actions

**Performance:**
- Permission check completes in <100ms (cached) or <500ms (uncached)
- Comment creation completes in <200ms
- WebSocket messages delivered in <100ms
- Version list loads in <1 second for 30 versions
- Page with comments panel loads in <2 seconds

**User Experience:**
- Share modal is intuitive, users can share in <30 seconds
- Comment interface is easy to use, users add comments in <15 seconds
- Mention autocomplete works smoothly (300ms delay max)
- Real-time updates feel instant (no noticeable delay)
- Permission errors are clear and actionable (tell user what's needed)
- Version history is understandable (clear change summaries)

**Security:**
- All permission checks enforced, no unauthorized access possible
- Share links cannot be brute-forced (cryptographically secure tokens)
- Comment content sanitized, no XSS vulnerabilities
- Rate limiting prevents abuse (invitations, shares, comments)
- Audit logs cannot be tampered with

**Testing:**
- Backend test coverage >85%
- Frontend test coverage >80%
- All E2E collaboration workflows pass
- Load test: 100+ concurrent WebSocket connections stable
- Security tests: No critical vulnerabilities found

**Documentation:**
- API documentation complete (OpenAPI/Swagger)
- Frontend component documentation (Storybook or comments)
- User guide for team collaboration features
- Admin guide for managing organizations and permissions
