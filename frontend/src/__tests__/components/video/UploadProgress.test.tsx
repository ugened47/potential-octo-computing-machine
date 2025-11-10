import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  UploadProgress,
  type UploadStatus,
} from "@/components/video/UploadProgress";

describe("UploadProgress", () => {
  it("renders progress bar with correct value", () => {
    render(<UploadProgress progress={50} status="uploading" />);

    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("shows preparing status text", () => {
    render(<UploadProgress progress={0} status="preparing" />);

    expect(screen.getByText("Preparing upload...")).toBeInTheDocument();
  });

  it("shows uploading status text", () => {
    render(<UploadProgress progress={30} status="uploading" />);

    expect(screen.getByText("Uploading...")).toBeInTheDocument();
  });

  it("shows processing status text", () => {
    render(<UploadProgress progress={90} status="processing" />);

    expect(screen.getByText("Processing...")).toBeInTheDocument();
  });

  it("shows complete status text", () => {
    render(<UploadProgress progress={100} status="complete" />);

    expect(screen.getByText("Upload complete!")).toBeInTheDocument();
  });

  it("shows error status text", () => {
    render(
      <UploadProgress progress={50} status="error" error="Upload failed" />,
    );

    expect(screen.getByText("Upload failed")).toBeInTheDocument();
  });

  it("displays upload speed when provided", () => {
    render(
      <UploadProgress progress={40} status="uploading" uploadSpeed={5.25} />,
    );

    expect(screen.getByText("Speed: 5.25 MB/s")).toBeInTheDocument();
  });

  it("displays estimated time remaining when provided", () => {
    render(
      <UploadProgress
        progress={40}
        status="uploading"
        estimatedTimeRemaining={45}
      />,
    );

    expect(screen.getByText(/Time remaining: 45s/)).toBeInTheDocument();
  });

  it("formats time remaining in minutes and seconds", () => {
    render(
      <UploadProgress
        progress={40}
        status="uploading"
        estimatedTimeRemaining={125}
      />,
    );

    expect(screen.getByText(/2m 5s/)).toBeInTheDocument();
  });

  it("displays error message when error prop is provided", () => {
    const errorMessage = "Network connection failed";
    render(
      <UploadProgress progress={50} status="error" error={errorMessage} />,
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("shows retry button on error with callback", () => {
    const onRetry = vi.fn();
    render(
      <UploadProgress
        progress={50}
        status="error"
        error="Upload failed"
        onRetry={onRetry}
      />,
    );

    const retryButton = screen.getByText("Retry Upload");
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("shows cancel button during preparation", () => {
    const onCancel = vi.fn();
    render(
      <UploadProgress progress={0} status="preparing" onCancel={onCancel} />,
    );

    const cancelButton = screen.getByText("Cancel");
    expect(cancelButton).toBeInTheDocument();

    fireEvent.click(cancelButton);
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("shows cancel button during upload", () => {
    const onCancel = vi.fn();
    render(
      <UploadProgress progress={30} status="uploading" onCancel={onCancel} />,
    );

    const cancelButton = screen.getByText("Cancel");
    expect(cancelButton).toBeInTheDocument();
  });

  it("does not show cancel button during processing", () => {
    render(
      <UploadProgress progress={90} status="processing" onCancel={vi.fn()} />,
    );

    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
  });

  it("does not show cancel button when complete", () => {
    render(
      <UploadProgress progress={100} status="complete" onCancel={vi.fn()} />,
    );

    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
  });

  it("does not show retry button when upload is successful", () => {
    render(
      <UploadProgress progress={100} status="complete" onRetry={vi.fn()} />,
    );

    expect(screen.queryByText("Retry Upload")).not.toBeInTheDocument();
  });

  it("shows correct icon for complete status", () => {
    const { container } = render(
      <UploadProgress progress={100} status="complete" />,
    );

    // Check for CheckCircle2 icon by class or data-testid
    const icon = container.querySelector(".text-green-600");
    expect(icon).toBeInTheDocument();
  });

  it("shows correct icon for error status", () => {
    const { container } = render(
      <UploadProgress progress={50} status="error" />,
    );

    const icon = container.querySelector(".text-destructive");
    expect(icon).toBeInTheDocument();
  });

  it("shows pulsing upload icon during upload", () => {
    const { container } = render(
      <UploadProgress progress={50} status="uploading" />,
    );

    const icon = container.querySelector(".animate-pulse");
    expect(icon).toBeInTheDocument();
  });

  it("renders without optional props", () => {
    render(<UploadProgress progress={25} status="uploading" />);

    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("Uploading...")).toBeInTheDocument();
  });

  it("handles 0% progress", () => {
    render(<UploadProgress progress={0} status="preparing" />);

    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("handles 100% progress", () => {
    render(<UploadProgress progress={100} status="complete" />);

    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("displays both speed and time remaining together", () => {
    render(
      <UploadProgress
        progress={50}
        status="uploading"
        uploadSpeed={3.5}
        estimatedTimeRemaining={60}
      />,
    );

    expect(screen.getByText("Speed: 3.50 MB/s")).toBeInTheDocument();
    expect(screen.getByText(/Time remaining: 1m 0s/)).toBeInTheDocument();
  });
});
