import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BatchUploadModal from "@/components/upload/BatchUploadModal";

// Mock fetch for API calls
global.fetch = vi.fn();

describe("BatchUploadModal", () => {
  const mockOnClose = vi.fn();
  const mockOnUploadComplete = vi.fn();
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onUploadComplete: mockOnUploadComplete,
  };

  // Create mock File objects
  const createMockFile = (name: string, size: number, type: string) => {
    const blob = new Blob(["x".repeat(size)], { type });
    return new File([blob], name, { type });
  };

  const mockVideoFiles = [
    createMockFile("video1.mp4", 1024 * 1024 * 10, "video/mp4"), // 10MB
    createMockFile("video2.mp4", 1024 * 1024 * 15, "video/mp4"), // 15MB
    createMockFile("video3.webm", 1024 * 1024 * 12, "video/webm"), // 12MB
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "upload-123", status: "processing" }),
    });
  });

  it("renders batch upload modal when open", () => {
    render(<BatchUploadModal {...defaultProps} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/batch upload/i)).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(<BatchUploadModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("allows selecting multiple video files", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    await waitFor(() => {
      expect(screen.getByText(/video1\.mp4/i)).toBeInTheDocument();
      expect(screen.getByText(/video2\.mp4/i)).toBeInTheDocument();
      expect(screen.getByText(/video3\.webm/i)).toBeInTheDocument();
    });
  });

  it("displays file count and total size", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    await waitFor(() => {
      expect(screen.getByText(/3 files/i)).toBeInTheDocument();
      expect(screen.getByText(/37.*mb/i)).toBeInTheDocument(); // 10+15+12 = 37MB
    });
  });

  it("validates file types - rejects non-video files", async () => {
    const user = userEvent.setup();
    const invalidFile = createMockFile("document.pdf", 1024, "application/pdf");

    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, [invalidFile]);

    await waitFor(() => {
      expect(
        screen.getByText(/only video files are allowed/i)
      ).toBeInTheDocument();
    });
  });

  it("validates file size - rejects files exceeding limit", async () => {
    const user = userEvent.setup();
    const largeFile = createMockFile(
      "large-video.mp4",
      1024 * 1024 * 1024 * 3, // 3GB
      "video/mp4"
    );

    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, [largeFile]);

    await waitFor(() => {
      expect(
        screen.getByText(/file size exceeds maximum/i)
      ).toBeInTheDocument();
    });
  });

  it("allows removing individual files from the list", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    await waitFor(() => {
      expect(screen.getByText(/video1\.mp4/i)).toBeInTheDocument();
    });

    // Find and click remove button for first file
    const removeButtons = screen.getAllByRole("button", { name: /remove/i });
    await user.click(removeButtons[0]);

    await waitFor(() => {
      expect(screen.queryByText(/video1\.mp4/i)).not.toBeInTheDocument();
      expect(screen.getByText(/2 files/i)).toBeInTheDocument();
    });
  });

  it("configures upload settings for all files", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    // Configure settings
    const autoProcessCheckbox = screen.getByLabelText(/auto-process videos/i);
    await user.click(autoProcessCheckbox);

    const removesilenceCheckbox = screen.getByLabelText(/remove silence/i);
    await user.click(removesilenceCheckbox);

    expect(autoProcessCheckbox).toBeChecked();
    expect(removesilenceCheckbox).toBeChecked();
  });

  it("displays upload progress for each file", async () => {
    const user = userEvent.setup();

    // Mock XMLHttpRequest for upload progress
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: {
        addEventListener: vi.fn((event, callback) => {
          if (event === "progress") {
            setTimeout(() => callback({ loaded: 50, total: 100 }), 10);
          }
        }),
      },
      addEventListener: vi.fn((event, callback) => {
        if (event === "load") {
          setTimeout(() => {
            (mockXHR as any).status = 200;
            (mockXHR as any).response = JSON.stringify({ id: "upload-123" });
            callback();
          }, 20);
        }
      }),
    };

    global.XMLHttpRequest = vi.fn(() => mockXHR) as any;

    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, [mockVideoFiles[0]]);

    const uploadButton = screen.getByRole("button", { name: /start upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      // Should show progress indicator
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
      expect(screen.getByText(/50%/i)).toBeInTheDocument();
    });
  });

  it("uploads all files when upload button is clicked", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    const uploadButton = screen.getByRole("button", { name: /start upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3);
    });
  });

  it("handles upload errors gracefully", async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockRejectedValueOnce(new Error("Upload failed"));

    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, [mockVideoFiles[0]]);

    const uploadButton = screen.getByRole("button", { name: /start upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
    });
  });

  it("calls onUploadComplete callback when all uploads finish", async () => {
    const user = userEvent.setup();
    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, mockVideoFiles);

    const uploadButton = screen.getByRole("button", { name: /start upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: "upload-123" }),
        ])
      );
    });
  });

  it("disables upload button when no files selected", () => {
    render(<BatchUploadModal {...defaultProps} />);

    const uploadButton = screen.getByRole("button", { name: /start upload/i });
    expect(uploadButton).toBeDisabled();
  });

  it("shows warning when uploading large number of files", async () => {
    const user = userEvent.setup();
    const manyFiles = Array.from({ length: 15 }, (_, i) =>
      createMockFile(`video${i}.mp4`, 1024 * 1024 * 5, "video/mp4")
    );

    render(<BatchUploadModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/select videos/i);
    await user.upload(fileInput, manyFiles);

    await waitFor(() => {
      expect(
        screen.getByText(/uploading many files.*may take some time/i)
      ).toBeInTheDocument();
    });
  });
});
