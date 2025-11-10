"use client";

import { useEffect, useMemo, useState } from "react";
import type { Transcript, WordTimestamp } from "@/types/transcript";
import { cn } from "@/lib/utils";

interface TranscriptDisplayProps {
  transcript: Transcript;
  currentTime?: number;
  onWordClick?: (timestamp: number) => void;
  searchQuery?: string;
}

export function TranscriptDisplay({
  transcript,
  currentTime = 0,
  onWordClick,
  searchQuery = "",
}: TranscriptDisplayProps) {
  const [highlightedWordIndex, setHighlightedWordIndex] = useState<
    number | null
  >(null);

  const words = transcript.word_timestamps?.words || [];

  // Find current word based on playback time
  useEffect(() => {
    if (words.length === 0) return;

    const currentIndex = words.findIndex(
      (word) => currentTime >= word.start && currentTime <= word.end,
    );

    if (currentIndex !== -1) {
      setHighlightedWordIndex(currentIndex);
      // Scroll to highlighted word
      const wordElement = document.getElementById(`word-${currentIndex}`);
      if (wordElement) {
        wordElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    } else {
      setHighlightedWordIndex(null);
    }
  }, [currentTime, words]);

  // Filter words by search query
  const filteredWords = useMemo(() => {
    if (!searchQuery.trim()) return words;

    const query = searchQuery.toLowerCase();
    return words.map((word, index) => ({
      ...word,
      index,
      matches: word.word.toLowerCase().includes(query),
    }));
  }, [words, searchQuery]);

  const handleWordClick = (word: WordTimestamp) => {
    if (onWordClick) {
      onWordClick(word.start);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="space-y-2">
        {/* Language and status info */}
        <div className="mb-4 flex items-center gap-4 text-sm text-muted-foreground">
          {transcript.language && (
            <span>Language: {transcript.language.toUpperCase()}</span>
          )}
          <span className="capitalize">Status: {transcript.status}</span>
        </div>

        {/* Transcript text */}
        <div className="flex flex-wrap gap-1 text-base leading-relaxed">
          {filteredWords.map((word, index) => {
            const isHighlighted = highlightedWordIndex === index;
            const isSearchMatch = "matches" in word && word.matches;

            return (
              <span
                key={index}
                id={`word-${index}`}
                className={cn(
                  "cursor-pointer rounded px-1 py-0.5 transition-colors",
                  {
                    "bg-primary text-primary-foreground": isHighlighted,
                    "bg-yellow-200 dark:bg-yellow-900":
                      isSearchMatch && !isHighlighted,
                    "hover:bg-accent": !isHighlighted && !isSearchMatch,
                  },
                )}
                onClick={() => handleWordClick(word)}
                title={`${word.word} (${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s)`}
              >
                {word.word}
              </span>
            );
          })}
        </div>

        {/* Full text fallback if word timestamps not available */}
        {words.length === 0 && (
          <div className="text-muted-foreground">{transcript.full_text}</div>
        )}
      </div>
    </div>
  );
}
