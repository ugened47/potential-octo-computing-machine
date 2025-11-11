import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HighlightsPanel from "@/components/highlights/HighlightsPanel";

// Mock fetch for API calls
global.fetch = vi.fn();

describe("HighlightsPanel", () => {
  const mockHighlights = [
    {
      id: "highlight-1",
      videoId: "video-123",
      startTime: 10.5,
      endTime: 25.3,
      score: 0.95,
      reason: "High engagement segment",
      duration: 14.8,
      thumbnail: "/thumbnails/highlight-1.jpg",
    },
    {
      id: "highlight-2",
      videoId: "video-123",
      startTime: 45.2,
      endTime: 62.8,
      score: 0.87,
      reason: "Key moment detected",
      duration: 17.6,
      thumbnail: "/thumbnails/highlight-2.jpg",
    },
    {
      id: "highlight-3",
      videoId: "video-123",
      startTime: 120.0,
      endTime: 135.5,
      score: 0.78,
      reason: "Important content",
      duration: 15.5,
      thumbnail: "/thumbnails/highlight-3.jpg",
    },
  ];

  const mockOnHighlightClick = vi.fn();
  const defaultProps = {
    videoId: "video-123",
    onHighlightClick: mockOnHighlightClick,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ highlights: mockHighlights }),
    });
  });

  it("displays loading state initially", () => {
    render(<HighlightsPanel {...defaultProps} />);

    expect(screen.getByText(/loading highlights/i)).toBeInTheDocument();
  });

  it("displays highlights after loading", async () => {
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/high engagement segment/i)).toBeInTheDocument();
      expect(screen.getByText(/key moment detected/i)).toBeInTheDocument();
      expect(screen.getByText(/important content/i)).toBeInTheDocument();
    });
  });

  it("displays empty state when no highlights found", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ highlights: [] }),
    });

    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/no highlights found/i)).toBeInTheDocument();
      expect(
        screen.getByText(/try adjusting your search/i)
      ).toBeInTheDocument();
    });
  });

  it("displays error state on failed fetch", async () => {
    (global.fetch as any).mockRejectedValueOnce(
      new Error("Failed to fetch highlights")
    );

    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(
        screen.getByText(/failed to load highlights/i)
      ).toBeInTheDocument();
    });
  });

  it("displays highlight scores and durations", async () => {
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/95%/i)).toBeInTheDocument(); // Score 0.95
      expect(screen.getByText(/87%/i)).toBeInTheDocument(); // Score 0.87
      expect(screen.getByText(/14\.8s/i)).toBeInTheDocument(); // Duration
      expect(screen.getByText(/17\.6s/i)).toBeInTheDocument(); // Duration
    });
  });

  it("filters highlights by minimum score", async () => {
    const user = userEvent.setup();
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getAllByRole("article")).toHaveLength(3);
    });

    // Find and adjust the score filter slider
    const scoreSlider = screen.getByLabelText(/minimum score/i);
    await user.type(scoreSlider, "0.85");

    await waitFor(() => {
      // Only highlights with score >= 0.85 should be visible
      expect(screen.getAllByRole("article")).toHaveLength(2);
      expect(screen.queryByText(/important content/i)).not.toBeInTheDocument();
    });
  });

  it("sorts highlights by score in descending order", async () => {
    const user = userEvent.setup();
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getAllByRole("article")).toHaveLength(3);
    });

    // Select sort by score
    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, "score-desc");

    await waitFor(() => {
      const highlights = screen.getAllByRole("article");
      // First highlight should be the one with highest score (0.95)
      expect(within(highlights[0]).getByText(/95%/i)).toBeInTheDocument();
    });
  });

  it("sorts highlights by duration in descending order", async () => {
    const user = userEvent.setup();
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getAllByRole("article")).toHaveLength(3);
    });

    // Select sort by duration
    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, "duration-desc");

    await waitFor(() => {
      const highlights = screen.getAllByRole("article");
      // First highlight should be the one with longest duration (17.6s)
      expect(within(highlights[0]).getByText(/17\.6s/i)).toBeInTheDocument();
    });
  });

  it("calls onHighlightClick when highlight is clicked", async () => {
    const user = userEvent.setup();
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/high engagement segment/i)).toBeInTheDocument();
    });

    const firstHighlight = screen.getByText(/high engagement segment/i);
    await user.click(firstHighlight);

    expect(mockOnHighlightClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "highlight-1",
        startTime: 10.5,
        endTime: 25.3,
      })
    );
  });

  it("displays highlight thumbnails", async () => {
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      const images = screen.getAllByRole("img");
      expect(images).toHaveLength(3);
      expect(images[0]).toHaveAttribute(
        "src",
        expect.stringContaining("highlight-1.jpg")
      );
    });
  });

  it("displays time range for each highlight", async () => {
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      // Check for formatted time ranges (e.g., "0:10 - 0:25")
      expect(screen.getByText(/0:10.*0:25/i)).toBeInTheDocument();
      expect(screen.getByText(/0:45.*1:02/i)).toBeInTheDocument();
      expect(screen.getByText(/2:00.*2:15/i)).toBeInTheDocument();
    });
  });

  it("allows exporting individual highlights", async () => {
    const user = userEvent.setup();
    render(<HighlightsPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getAllByRole("article")).toHaveLength(3);
    });

    // Find export button for first highlight
    const exportButtons = screen.getAllByRole("button", { name: /export/i });
    await user.click(exportButtons[0]);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/highlights/highlight-1/export"),
        expect.any(Object)
      );
    });
  });
});
