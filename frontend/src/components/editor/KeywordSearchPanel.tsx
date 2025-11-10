"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useToast } from "@/components/ui/use-toast";
import {
  searchKeyword,
  createClip,
  getClipProgress,
  type KeywordMatch,
} from "@/lib/clip-api";
import { formatTime } from "@/lib/utils";
import { Search, Scissors, AlertCircle } from "lucide-react";

interface KeywordSearchPanelProps {
  videoId: string;
  onClipCreated?: () => void;
}

export function KeywordSearchPanel({
  videoId,
  onClipCreated,
}: KeywordSearchPanelProps) {
  const { toast } = useToast();

  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState<KeywordMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!keyword.trim()) {
      toast({
        title: "Error",
        description: "Please enter a keyword to search",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setSearched(true);

    try {
      const data = await searchKeyword(videoId, keyword.trim());
      setResults(data.matches);

      if (data.matches.length === 0) {
        toast({
          title: "No matches found",
          description: `No results found for "${keyword}"`,
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to search for keyword",
        variant: "destructive",
      });
      console.error("Failed to search:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateClip = async (match: KeywordMatch) => {
    setGenerating(match.id);

    try {
      const result = await createClip(videoId, {
        start: match.start,
        end: match.end,
        title: `Clip: ${keyword}`,
      });

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await getClipProgress(videoId, result.job_id);

          if (status.status === "completed") {
            clearInterval(pollInterval);
            setGenerating(null);
            toast({
              title: "Success",
              description: "Clip created successfully",
            });
            if (onClipCreated) {
              onClipCreated();
            }
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setGenerating(null);
            toast({
              title: "Error",
              description: status.message || "Failed to create clip",
              variant: "destructive",
            });
          }
        } catch (error) {
          clearInterval(pollInterval);
          setGenerating(null);
          console.error("Failed to check clip progress:", error);
        }
      }, 1000);

      // Cleanup after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (generating === match.id) {
          setGenerating(null);
        }
      }, 300000);
    } catch (error) {
      setGenerating(null);
      toast({
        title: "Error",
        description: "Failed to create clip",
        variant: "destructive",
      });
      console.error("Failed to generate clip:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      handleSearch();
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter keyword or phrase to search..."
            className="pl-10"
            disabled={loading}
          />
        </div>
        <Button onClick={handleSearch} disabled={loading || !keyword.trim()}>
          {loading ? <LoadingSpinner /> : "Search"}
        </Button>
      </div>

      {/* Results */}
      {searched && (
        <div className="space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
              <span className="ml-2 text-sm text-muted-foreground">
                Searching transcript...
              </span>
            </div>
          ) : results.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Found {results.length} match{results.length !== 1 ? "es" : ""}
                </p>
              </div>

              <div className="space-y-2">
                {results.map((match) => (
                  <Card
                    key={match.id}
                    className="hover:shadow-md transition-shadow"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 space-y-2">
                          {/* Timestamp */}
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">
                              {formatTime(match.start)}
                            </Badge>
                            {match.confidence && (
                              <Badge variant="outline" className="text-xs">
                                {Math.round(match.confidence * 100)}% match
                              </Badge>
                            )}
                          </div>

                          {/* Excerpt */}
                          <p className="text-sm leading-relaxed">
                            {match.excerpt}
                          </p>

                          {/* Duration */}
                          <p className="text-xs text-muted-foreground">
                            Duration: {(match.end - match.start).toFixed(1)}s
                          </p>
                        </div>

                        {/* Create Clip Button */}
                        <Button
                          size="sm"
                          onClick={() => handleGenerateClip(match)}
                          disabled={generating === match.id}
                          className="shrink-0"
                        >
                          {generating === match.id ? (
                            <>
                              <LoadingSpinner />
                              <span className="ml-2">Creating...</span>
                            </>
                          ) : (
                            <>
                              <Scissors className="h-3 w-3 mr-1" />
                              Create Clip
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-8 space-y-2">
              <AlertCircle className="h-8 w-8 mx-auto text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">
                No matches found for &quot;{keyword}&quot;
              </p>
              <p className="text-xs text-muted-foreground">
                Try a different keyword or phrase
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
