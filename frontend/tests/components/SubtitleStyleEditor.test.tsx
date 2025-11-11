import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SubtitleStyleEditor from "@/components/subtitles/SubtitleStyleEditor";

describe("SubtitleStyleEditor", () => {
  const mockOnStyleChange = vi.fn();
  const defaultStyle = {
    fontFamily: "Arial",
    fontSize: 24,
    fontWeight: "normal",
    fontStyle: "normal",
    color: "#FFFFFF",
    backgroundColor: "#000000",
    opacity: 0.8,
    textAlign: "center",
    position: "bottom",
    padding: 10,
    borderRadius: 5,
    shadow: true,
    shadowColor: "#000000",
    shadowBlur: 3,
  };

  const defaultProps = {
    style: defaultStyle,
    onStyleChange: mockOnStyleChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders subtitle style editor", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    expect(screen.getByText(/subtitle style/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/font family/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/font size/i)).toBeInTheDocument();
  });

  it("displays current font family", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    const fontSelect = screen.getByLabelText(/font family/i);
    expect(fontSelect).toHaveValue("Arial");
  });

  it("changes font family", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const fontSelect = screen.getByLabelText(/font family/i);
    await user.selectOptions(fontSelect, "Helvetica");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontFamily: "Helvetica",
      })
    );
  });

  it("displays font size slider", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    const fontSizeSlider = screen.getByLabelText(/font size/i);
    expect(fontSizeSlider).toHaveValue("24");
  });

  it("adjusts font size using slider", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const fontSizeSlider = screen.getByLabelText(/font size/i);
    await user.clear(fontSizeSlider);
    await user.type(fontSizeSlider, "32");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontSize: 32,
      })
    );
  });

  it("toggles font weight between normal and bold", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const boldButton = screen.getByRole("button", { name: /bold/i });
    await user.click(boldButton);

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontWeight: "bold",
      })
    );
  });

  it("toggles font style between normal and italic", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const italicButton = screen.getByRole("button", { name: /italic/i });
    await user.click(italicButton);

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontStyle: "italic",
      })
    );
  });

  it("displays color picker for text color", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    const colorPicker = screen.getByLabelText(/text color/i);
    expect(colorPicker).toHaveValue("#ffffff");
  });

  it("changes text color using color picker", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const colorPicker = screen.getByLabelText(/text color/i);
    await user.click(colorPicker);
    // Simulate color selection
    await user.clear(colorPicker);
    await user.type(colorPicker, "#FF0000");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        color: "#FF0000",
      })
    );
  });

  it("displays color picker for background color", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    const bgColorPicker = screen.getByLabelText(/background color/i);
    expect(bgColorPicker).toHaveValue("#000000");
  });

  it("changes background color", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const bgColorPicker = screen.getByLabelText(/background color/i);
    await user.clear(bgColorPicker);
    await user.type(bgColorPicker, "#0000FF");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        backgroundColor: "#0000FF",
      })
    );
  });

  it("adjusts opacity slider", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const opacitySlider = screen.getByLabelText(/opacity/i);
    await user.clear(opacitySlider);
    await user.type(opacitySlider, "0.5");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        opacity: 0.5,
      })
    );
  });

  it("changes text alignment", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const alignmentButtons = screen.getAllByRole("button");
    const leftAlignButton = alignmentButtons.find((btn) =>
      btn.textContent?.includes("Left")
    );

    if (leftAlignButton) {
      await user.click(leftAlignButton);

      expect(mockOnStyleChange).toHaveBeenCalledWith(
        expect.objectContaining({
          textAlign: "left",
        })
      );
    }
  });

  it("changes subtitle position", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const positionSelect = screen.getByLabelText(/position/i);
    await user.selectOptions(positionSelect, "top");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        position: "top",
      })
    );
  });

  it("displays style presets", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    expect(screen.getByText(/presets/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /default/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /bold/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /minimal/i })).toBeInTheDocument();
  });

  it("applies preset style when selected", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const boldPresetButton = screen.getByRole("button", { name: /bold preset/i });
    await user.click(boldPresetButton);

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontWeight: "bold",
        fontSize: expect.any(Number),
      })
    );
  });

  it("displays live preview of subtitle style", () => {
    render(<SubtitleStyleEditor {...defaultProps} />);

    const preview = screen.getByTestId("subtitle-preview");
    expect(preview).toBeInTheDocument();
    expect(preview).toHaveStyle({
      fontFamily: "Arial",
      fontSize: "24px",
      color: "#FFFFFF",
    });
  });

  it("updates preview when style changes", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<SubtitleStyleEditor {...defaultProps} />);

    const fontSelect = screen.getByLabelText(/font family/i);
    await user.selectOptions(fontSelect, "Helvetica");

    // Rerender with updated style
    rerender(
      <SubtitleStyleEditor
        {...defaultProps}
        style={{ ...defaultStyle, fontFamily: "Helvetica" }}
      />
    );

    const preview = screen.getByTestId("subtitle-preview");
    expect(preview).toHaveStyle({
      fontFamily: "Helvetica",
    });
  });

  it("toggles text shadow", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const shadowCheckbox = screen.getByLabelText(/text shadow/i);
    await user.click(shadowCheckbox);

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        shadow: false,
      })
    );
  });

  it("adjusts shadow blur when shadow is enabled", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const shadowBlurSlider = screen.getByLabelText(/shadow blur/i);
    await user.clear(shadowBlurSlider);
    await user.type(shadowBlurSlider, "5");

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        shadowBlur: 5,
      })
    );
  });

  it("allows resetting to default styles", async () => {
    const user = userEvent.setup();
    render(<SubtitleStyleEditor {...defaultProps} />);

    const resetButton = screen.getByRole("button", { name: /reset/i });
    await user.click(resetButton);

    expect(mockOnStyleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fontFamily: expect.any(String),
        fontSize: expect.any(Number),
        color: expect.any(String),
      })
    );
  });
});
