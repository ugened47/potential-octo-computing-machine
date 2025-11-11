/**
 * Team Collaboration Components Tests
 *
 * Unit tests for collaboration components.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OrganizationManager } from '../OrganizationManager';
import { MembersPanel } from '../MembersPanel';
import { ShareModal } from '../ShareModal';
import { CommentsPanel } from '../CommentsPanel';
import { ActiveUsers } from '../ActiveUsers';
import { NotificationBell } from '../NotificationBell';
import * as collaborationApi from '@/lib/api/collaboration';

// Mock the API
vi.mock('@/lib/api/collaboration');
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: true,
    isConnecting: false,
    error: null,
    send: vi.fn(),
    joinRoom: vi.fn(),
    leaveRoom: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
  usePresence: () => ({
    activeUsers: [],
    isConnected: true,
  }),
  useRealtimeComments: () => ({}),
  useTypingIndicator: () => ({
    typingUsers: [],
    sendTypingIndicator: vi.fn(),
  }),
  useRealtimeNotifications: () => ({}),
}));

describe('OrganizationManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders organization list', async () => {
    const mockOrgs = [
      {
        id: '1',
        name: 'Test Org',
        slug: 'test-org',
        owner_id: 'user1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        member_count: 5,
      },
    ];

    vi.spyOn(collaborationApi, 'getOrganizations').mockResolvedValue(mockOrgs);

    render(<OrganizationManager />);

    await waitFor(() => {
      expect(screen.getByText('Test Org')).toBeInTheDocument();
    });
  });

  it('opens create dialog when clicking new organization', async () => {
    vi.spyOn(collaborationApi, 'getOrganizations').mockResolvedValue([]);

    render(<OrganizationManager />);

    const newButton = await screen.findByText('New Organization');
    fireEvent.click(newButton);

    await waitFor(() => {
      expect(screen.getByText('Create Organization')).toBeInTheDocument();
    });
  });
});

describe('MembersPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders team members', async () => {
    const mockMembers = [
      {
        id: '1',
        organization_id: 'org1',
        user_id: 'user1',
        role: 'admin' as const,
        joined_at: new Date().toISOString(),
        user: {
          id: 'user1',
          email: 'test@example.com',
          name: 'Test User',
        },
      },
    ];

    vi.spyOn(collaborationApi, 'getTeamMembers').mockResolvedValue(mockMembers);

    render(<MembersPanel organizationId="org1" />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  it('opens invite dialog when clicking invite member', async () => {
    vi.spyOn(collaborationApi, 'getTeamMembers').mockResolvedValue([]);

    render(<MembersPanel organizationId="org1" />);

    const inviteButton = await screen.findByText('Invite Member');
    fireEvent.click(inviteButton);

    await waitFor(() => {
      expect(screen.getByText('Invite Team Member')).toBeInTheDocument();
    });
  });
});

describe('ShareModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders share modal when open', () => {
    vi.spyOn(collaborationApi, 'getShares').mockResolvedValue([]);

    render(
      <ShareModal
        isOpen={true}
        onClose={vi.fn()}
        resourceType="video"
        resourceId="video1"
        resourceTitle="Test Video"
      />
    );

    expect(screen.getByText('Share Test Video')).toBeInTheDocument();
  });

  it('has tabs for people and link sharing', async () => {
    vi.spyOn(collaborationApi, 'getShares').mockResolvedValue([]);

    render(
      <ShareModal
        isOpen={true}
        onClose={vi.fn()}
        resourceType="video"
        resourceId="video1"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Share with People')).toBeInTheDocument();
      expect(screen.getByText('Share via Link')).toBeInTheDocument();
    });
  });
});

describe('CommentsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders comments panel', async () => {
    vi.spyOn(collaborationApi, 'getCommentThreads').mockResolvedValue([]);

    render(
      <CommentsPanel resourceType="video" resourceId="video1" />
    );

    await waitFor(() => {
      expect(screen.getByText('Comments')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Add a comment...')).toBeInTheDocument();
    });
  });

  it('displays comment threads', async () => {
    const mockThreads = [
      {
        parent: {
          id: 'comment1',
          resource_type: 'video' as const,
          resource_id: 'video1',
          user_id: 'user1',
          content: 'Test comment',
          resolved: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          edited: false,
          user: {
            id: 'user1',
            email: 'test@example.com',
            name: 'Test User',
          },
        },
        replies: [],
      },
    ];

    vi.spyOn(collaborationApi, 'getCommentThreads').mockResolvedValue(
      mockThreads
    );

    render(
      <CommentsPanel resourceType="video" resourceId="video1" />
    );

    await waitFor(() => {
      expect(screen.getByText('Test comment')).toBeInTheDocument();
    });
  });
});

describe('ActiveUsers', () => {
  it('renders nothing when no active users', () => {
    const { container } = render(
      <ActiveUsers resourceType="video" resourceId="video1" />
    );

    expect(container.firstChild).toBeNull();
  });
});

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders notification bell', () => {
    vi.spyOn(collaborationApi, 'getUnreadNotificationCount').mockResolvedValue(
      0
    );

    render(<NotificationBell />);

    const bellButton = screen.getByRole('button');
    expect(bellButton).toBeInTheDocument();
  });

  it('displays unread count badge', async () => {
    vi.spyOn(collaborationApi, 'getUnreadNotificationCount').mockResolvedValue(
      5
    );

    render(<NotificationBell />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });
});
