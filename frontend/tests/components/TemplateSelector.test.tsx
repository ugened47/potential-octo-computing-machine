import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TemplateSelector from "@/components/export/TemplateSelector";

describe("TemplateSelector", () => {
  const mockOnTemplateSelect = vi.fn();
  const defaultProps = {
    onTemplateSelect: mockOnTemplateSelect,
  };

  const platformTemplates = [
    {
      id: "youtube-shorts",
      name: "YouTube Shorts",
      platform: "youtube",
      aspectRatio: "9:16",
      resolution: "1080x1920",
      maxDuration: 60,
      icon: "youtube",
    },
    {
      id: "instagram-reel",
      name: "Instagram Reel",
      platform: "instagram",
      aspectRatio: "9:16",
      resolution: "1080x1920",
      maxDuration: 90,
      icon: "instagram",
    },
    {
      id: "tiktok",
      name: "TikTok",
      platform: "tiktok",
      aspectRatio: "9:16",
      resolution: "1080x1920",
      maxDuration: 180,
      icon: "tiktok",
    },
    {
      id: "twitter-video",
      name: "Twitter Video",
      platform: "twitter",
      aspectRatio: "16:9",
      resolution: "1280x720",
      maxDuration: 140,
      icon: "twitter",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders template selector", () => {
    render(<TemplateSelector {...defaultProps} />);

    expect(screen.getByText(/select template/i)).toBeInTheDocument();
  });

  it("displays platform preset templates", () => {
    render(<TemplateSelector {...defaultProps} />);

    expect(screen.getByText(/youtube shorts/i)).toBeInTheDocument();
    expect(screen.getByText(/instagram reel/i)).toBeInTheDocument();
    expect(screen.getByText(/tiktok/i)).toBeInTheDocument();
    expect(screen.getByText(/twitter video/i)).toBeInTheDocument();
  });

  it("displays template details including aspect ratio and resolution", () => {
    render(<TemplateSelector {...defaultProps} />);

    expect(screen.getByText(/9:16/)).toBeInTheDocument();
    expect(screen.getByText(/1080x1920/)).toBeInTheDocument();
    expect(screen.getByText(/16:9/)).toBeInTheDocument();
    expect(screen.getByText(/1280x720/)).toBeInTheDocument();
  });

  it("displays maximum duration for each template", () => {
    render(<TemplateSelector {...defaultProps} />);

    expect(screen.getByText(/60.*sec/i)).toBeInTheDocument(); // YouTube Shorts
    expect(screen.getByText(/90.*sec/i)).toBeInTheDocument(); // Instagram Reel
    expect(screen.getByText(/180.*sec/i)).toBeInTheDocument(); // TikTok
  });

  it("selects a template when clicked", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const youtubeTemplate = screen.getByText(/youtube shorts/i);
    await user.click(youtubeTemplate);

    expect(mockOnTemplateSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "youtube-shorts",
        platform: "youtube",
        aspectRatio: "9:16",
      })
    );
  });

  it("highlights selected template", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const youtubeTemplate = screen.getByText(/youtube shorts/i).closest("div");
    await user.click(youtubeTemplate!);

    expect(youtubeTemplate).toHaveClass(/selected|active/i);
  });

  it("displays template preview when template is selected", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const youtubeTemplate = screen.getByText(/youtube shorts/i);
    await user.click(youtubeTemplate);

    // Preview should show aspect ratio visualization
    const preview = screen.getByTestId("template-preview");
    expect(preview).toBeInTheDocument();
    expect(preview).toHaveAttribute("data-aspect-ratio", "9:16");
  });

  it("allows creating custom template", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const customButton = screen.getByRole("button", { name: /custom template/i });
    await user.click(customButton);

    expect(screen.getByText(/create custom template/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/template name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/aspect ratio/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/resolution/i)).toBeInTheDocument();
  });

  it("validates custom template input", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const customButton = screen.getByRole("button", { name: /custom template/i });
    await user.click(customButton);

    // Try to submit without required fields
    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(
      screen.getByText(/please fill all required fields/i)
    ).toBeInTheDocument();
  });

  it("creates custom template with valid input", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const customButton = screen.getByRole("button", { name: /custom template/i });
    await user.click(customButton);

    // Fill in custom template form
    const nameInput = screen.getByLabelText(/template name/i);
    await user.type(nameInput, "My Custom Template");

    const aspectRatioSelect = screen.getByLabelText(/aspect ratio/i);
    await user.selectOptions(aspectRatioSelect, "4:3");

    const resolutionInput = screen.getByLabelText(/resolution/i);
    await user.type(resolutionInput, "1024x768");

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(mockOnTemplateSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "My Custom Template",
        aspectRatio: "4:3",
        resolution: "1024x768",
      })
    );
  });

  it("filters templates by platform", async () => {
    const user = userEvent.setup();
    render(<TemplateSelector {...defaultProps} />);

    const platformFilter = screen.getByLabelText(/filter by platform/i);
    await user.selectOptions(platformFilter, "youtube");

    // Only YouTube templates should be visible
    expect(screen.getByText(/youtube shorts/i)).toBeInTheDocument();
    expect(screen.queryByText(/instagram reel/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/tiktok/i)).not.toBeInTheDocument();
  });
});
