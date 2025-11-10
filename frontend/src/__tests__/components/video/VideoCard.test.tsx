import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VideoCard } from "@/components/video/VideoCard";
import type { Video } from "@/types/video";

// Mock router
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe("VideoCard", () => {
  const mockVideo: Video = {
    id: "123",
    title: "Test Video",
    status: "completed",
    thumbnail_url: "https://example.com/thumb.jpg",
    duration: 120.5,
    file_size: 50 * 1024 * 1024, // 50MB
    created_at: "2024-01-15T10:00:00Z",
    user_id: "user-1",
  };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders video card with all information", () => {
    render(<VideoCard video={mockVideo} />);

    expect(screen.getByText("Test Video")).toBeInTheDocument();
    expect(screen.getByText(/Duration:/)).toBeInTheDocument();
    expect(screen.getByText(/Size:/)).toBeInTheDocument();
    expect(screen.getByText(/Uploaded:/)).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("renders thumbnail when available", () => {
    render(<VideoCard video={mockVideo} />);

    const thumbnail = screen.getByAltText("Test Video");
    expect(thumbnail).toBeInTheDocument();
    expect(thumbnail).toHaveAttribute("src", mockVideo.thumbnail_url);
  });

  it("renders placeholder when no thumbnail", () => {
    const videoWithoutThumbnail = { ...mockVideo, thumbnail_url: null };
    render(<VideoCard video={videoWithoutThumbnail} />);

    // Should render Play icon placeholder
    const playIcons = screen.getAllByTestId("lucide-play");
    expect(playIcons.length).toBeGreaterThan(0);
  });

  it("navigates to video detail page on card click", () => {
    render(<VideoCard video={mockVideo} />);

    const card = screen.getByText("Test Video").closest("div")?.parentElement;
    fireEvent.click(card!);

    expect(mockPush).toHaveBeenCalledWith("/videos/123");
  });

  it("calls onDelete when delete button is clicked", () => {
    const onDelete = vi.fn();
    render(<VideoCard video={mockVideo} onDelete={onDelete} />);

    const deleteButton = screen.getByTitle("Delete");
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith("123");
    expect(mockPush).not.toHaveBeenCalled(); // Should not navigate
  });

  it("calls onEdit when edit button is clicked", () => {
    const onEdit = vi.fn();
    render(<VideoCard video={mockVideo} onEdit={onEdit} />);

    const editButton = screen.getByTitle("Edit");
    fireEvent.click(editButton);

    expect(onEdit).toHaveBeenCalledWith("123");
    expect(mockPush).not.toHaveBeenCalled(); // Should not navigate
  });

  it("shows correct badge variant for completed status", () => {
    render(<VideoCard video={mockVideo} />);

    const badge = screen.getByText("completed");
    expect(badge).toBeInTheDocument();
  });

  it("shows correct badge variant for processing status", () => {
    const processingVideo = { ...mockVideo, status: "processing" };
    render(<VideoCard video={processingVideo} />);

    const badges = screen.getAllByText("Processing");
    expect(badges.length).toBeGreaterThan(0);
  });

  it("shows correct badge variant for failed status", () => {
    const failedVideo = { ...mockVideo, status: "failed" };
    render(<VideoCard video={failedVideo} />);

    const badge = screen.getByText("failed");
    expect(badge).toBeInTheDocument();
  });

  it("shows processing overlay when status is processing", () => {
    const processingVideo = { ...mockVideo, status: "processing" };
    render(<VideoCard video={processingVideo} />);

    const processingBadges = screen.getAllByText("Processing");
    expect(processingBadges.length).toBeGreaterThan(0);
  });

  it("renders without optional callbacks", () => {
    render(<VideoCard video={mockVideo} />);

    // Should render without errors
    expect(screen.getByText("Test Video")).toBeInTheDocument();
  });

  it("handles missing optional video fields", () => {
    const minimalVideo: Video = {
      id: "456",
      title: "Minimal Video",
      status: "uploaded",
      created_at: "2024-01-15T10:00:00Z",
      user_id: "user-1",
    };

    render(<VideoCard video={minimalVideo} />);

    expect(screen.getByText("Minimal Video")).toBeInTheDocument();
    expect(screen.getByText("uploaded")).toBeInTheDocument();
  });

  it("truncates long titles with line-clamp", () => {
    const longTitleVideo = {
      ...mockVideo,
      title:
        "This is a very long video title that should be truncated when it exceeds the maximum length allowed in the card component",
    };

    const { container } = render(<VideoCard video={longTitleVideo} />);

    const titleElement = container.querySelector(".line-clamp-2");
    expect(titleElement).toBeInTheDocument();
  });

  it("shows hover effect with play icon overlay", () => {
    const { container } = render(<VideoCard video={mockVideo} />);

    const overlay = container.querySelector(".hover\\:opacity-100");
    expect(overlay).toBeInTheDocument();
  });
});
