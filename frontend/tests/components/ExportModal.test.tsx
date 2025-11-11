import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ExportModal from "@/components/export/ExportModal";

// Mock fetch for API calls
global.fetch = vi.fn();

describe("ExportModal", () => {
  const mockOnClose = vi.fn();
  const mockOnExportCreated = vi.fn();
  const defaultProps = {
    videoId: "test-video-123",
    isOpen: true,
    onClose: mockOnClose,
    onExportCreated: mockOnExportCreated,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "export-123", status: "pending" }),
    });
  });

  it("renders export modal when open", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/export video/i)).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(<ExportModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("displays resolution options", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByText(/resolution/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/1080p/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/720p/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/480p/i)).toBeInTheDocument();
  });

  it("displays quality options", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByText(/quality/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/high/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/medium/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/low/i)).toBeInTheDocument();
  });

  it("displays format/export type options", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByText(/format/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mp4/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/webm/i)).toBeInTheDocument();
  });

  it("selects resolution option", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const resolution1080 = screen.getByLabelText(/1080p/i);
    await user.click(resolution1080);

    expect(resolution1080).toBeChecked();
  });

  it("selects quality option", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const qualityHigh = screen.getByLabelText(/high/i);
    await user.click(qualityHigh);

    expect(qualityHigh).toBeChecked();
  });

  it("selects format option", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const formatMp4 = screen.getByLabelText(/mp4/i);
    await user.click(formatMp4);

    expect(formatMp4).toBeChecked();
  });

  it("submits export with selected options", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    // Select options
    await user.click(screen.getByLabelText(/1080p/i));
    await user.click(screen.getByLabelText(/high/i));
    await user.click(screen.getByLabelText(/mp4/i));

    // Submit form
    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/videos/test-video-123/export"),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: expect.stringContaining('"resolution":"1080p"'),
        })
      );
    });
  });

  it("calls onExportCreated callback on successful export", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(mockOnExportCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "export-123",
          status: "pending",
        })
      );
    });
  });

  it("displays error message on failed export", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Export failed" }),
    });

    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText(/export failed/i)).toBeInTheDocument();
    });
  });

  it("validates required fields before submission", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    // Try to submit without selecting any options
    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    // Should show validation error or button should be disabled
    const errorMessage = screen.queryByText(/please select all options/i);
    const isButtonDisabled = exportButton.hasAttribute("disabled");

    expect(errorMessage || isButtonDisabled).toBeTruthy();
  });

  it("disables submit button while exporting", async () => {
    // Delay the fetch response
    (global.fetch as any).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ id: "export-123" }),
              }),
            100
          )
        )
    );

    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    await user.click(screen.getByLabelText(/1080p/i));

    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    // Button should be disabled during export
    expect(exportButton).toBeDisabled();
  });

  it("displays loading state during export", async () => {
    // Delay the fetch response
    (global.fetch as any).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ id: "export-123" }),
              }),
            100
          )
        )
    );

    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    await user.click(screen.getByLabelText(/1080p/i));

    const exportButton = screen.getByRole("button", { name: /export/i });
    await user.click(exportButton);

    // Should show loading indicator
    expect(screen.getByText(/exporting/i)).toBeInTheDocument();
  });

  it("closes modal when close button is clicked", async () => {
    const user = userEvent.setup();
    render(<ExportModal {...defaultProps} />);

    const closeButton = screen.getByRole("button", { name: /close/i });
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("displays estimated file size based on selected options", () => {
    render(<ExportModal {...defaultProps} />);

    // Component should calculate and display estimated file size
    // based on video duration, resolution, and quality
    expect(screen.getByText(/estimated size/i)).toBeInTheDocument();
  });
});
