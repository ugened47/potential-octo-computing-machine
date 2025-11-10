export interface FAQItem {
  question: string;
  answer: string;
  category: "general" | "upload" | "processing" | "editing" | "export";
}

export const faqData: FAQItem[] = [
  {
    category: "general",
    question: "What video formats are supported?",
    answer:
      "We support MP4, MOV, AVI, WebM, and MKV formats. Maximum file size is 2GB.",
  },
  {
    category: "general",
    question: "How long does video processing take?",
    answer:
      "Processing time depends on video length. A 30-minute video typically takes about 5 minutes to transcribe and process.",
  },
  {
    category: "upload",
    question: "What is the maximum file size?",
    answer:
      "The maximum file size is 2GB per video. For larger files, consider compressing them before upload.",
  },
  {
    category: "upload",
    question: "Can I upload multiple videos at once?",
    answer:
      "Currently, you can upload one video at a time. Batch upload functionality is coming soon.",
  },
  {
    category: "processing",
    question: "How accurate is the transcription?",
    answer:
      "Our AI-powered transcription uses OpenAI Whisper, which provides over 90% accuracy for clear audio. Accuracy may vary with background noise or accents.",
  },
  {
    category: "processing",
    question: "What happens if transcription fails?",
    answer:
      "If transcription fails, you can retry the process. The system will automatically retry once, and you can manually retry from the video detail page.",
  },
  {
    category: "editing",
    question: "How do I create clips from my video?",
    answer:
      "Use the keyword search feature to find specific moments, then select the results to create clips. You can also manually select segments in the timeline editor.",
  },
  {
    category: "editing",
    question: "Can I edit the transcript?",
    answer:
      "Currently, transcripts are automatically generated and cannot be edited. Manual editing is planned for a future release.",
  },
  {
    category: "export",
    question: "What export formats are available?",
    answer:
      "You can export videos in MP4 format with various quality settings (720p, 1080p). Transcripts can be exported as SRT or VTT files.",
  },
  {
    category: "export",
    question: "How long does export take?",
    answer:
      "Export time depends on video length and selected segments. A 5-minute clip typically takes 1-2 minutes to export.",
  },
];
