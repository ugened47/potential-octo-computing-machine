"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatsCards } from "@/components/video/StatsCards";
import { StatsCardsSkeleton } from "@/components/video/StatsCardsSkeleton";
import { VideoGrid } from "@/components/video/VideoGrid";
import { VideoList } from "@/components/video/VideoList";
import { VideoCardSkeleton } from "@/components/video/VideoCardSkeleton";
import { ProcessingQueue } from "@/components/video/ProcessingQueue";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, Search, Grid3x3, List } from "lucide-react";
import { getVideos, deleteVideo, getDashboardStats } from "@/lib/video-api";
import { useOnboarding } from "@/store/onboarding-store";
import { useDebounce } from "@/hooks/useDebounce";
import type {
  Video,
  VideoListParams,
  DashboardStats,
  VideoStatus,
} from "@/types/video";

type ViewMode = "grid" | "list";

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isCompleted: onboardingCompleted } = useOnboarding();
  const [videos, setVideos] = useState<Video[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const [statusFilter, setStatusFilter] = useState<VideoStatus | "all">("all");
  const [sortBy, setSortBy] = useState<"created_at" | "title" | "duration">(
    "created_at",
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<string | null>(null);

  // Load view mode preference from localStorage
  useEffect(() => {
    const savedViewMode = localStorage.getItem(
      "dashboard-view-mode",
    ) as ViewMode | null;
    if (savedViewMode === "grid" || savedViewMode === "list") {
      setViewMode(savedViewMode);
    }
  }, []);

  // Redirect to onboarding if not completed (only for authenticated users)
  useEffect(() => {
    // Only redirect if we're sure the user is authenticated and onboarding isn't completed
    // This check happens after ProtectedRoute ensures authentication
    if (onboardingCompleted === false) {
      router.push("/onboarding");
    }
  }, [onboardingCompleted, router]);

  // Load filters from URL params
  useEffect(() => {
    const statusParam = searchParams.get("status") as VideoStatus | null;
    if (statusParam) {
      setStatusFilter(statusParam);
    }
  }, [searchParams]);

  const fetchVideos = async () => {
    try {
      setIsLoading(true);
      const params: VideoListParams = {
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 50,
        offset: 0,
      };

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      if (debouncedSearchQuery.trim()) {
        params.search = debouncedSearchQuery.trim();
      }

      const fetchedVideos = await getVideos(params);
      setVideos(fetchedVideos);
    } catch (error) {
      console.error("Failed to fetch videos:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const fetchedStats = await getDashboardStats();
      setStats(fetchedStats);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  useEffect(() => {
    fetchVideos();
    fetchStats();
  }, [statusFilter, sortBy, sortOrder, debouncedSearchQuery]);

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem("dashboard-view-mode", mode);
  }, []);

  const handleDeleteClick = useCallback((videoId: string) => {
    setVideoToDelete(videoId);
    setDeleteDialogOpen(true);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (!videoToDelete) return;

    try {
      await deleteVideo(videoToDelete);
      setDeleteDialogOpen(false);
      setVideoToDelete(null);
      fetchVideos();
      fetchStats();
    } catch (error) {
      console.error("Failed to delete video:", error);
      alert("Failed to delete video. Please try again.");
    }
  }, [videoToDelete]);

  const handleEdit = useCallback(
    (videoId: string) => {
      router.push(`/videos/${videoId}/edit`);
    },
    [router],
  );

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <Button onClick={() => router.push("/upload")}>
            <Upload className="mr-2 h-4 w-4" />
            Upload Video
          </Button>
        </div>

        {/* Stats Cards */}
        {stats ? <StatsCards stats={stats} /> : <StatsCardsSkeleton />}

        {/* Filters and Search */}
        <div className="mt-8 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search videos by title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select
              value={statusFilter}
              onValueChange={(value) =>
                setStatusFilter(value as VideoStatus | "all")
              }
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="uploaded">Uploaded</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={`${sortBy}-${sortOrder}`}
              onValueChange={(value) => {
                const [by, order] = value.split("-");
                setSortBy(by as "created_at" | "title" | "duration");
                setSortOrder(order as "asc" | "desc");
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_at-desc">Newest First</SelectItem>
                <SelectItem value="created_at-asc">Oldest First</SelectItem>
                <SelectItem value="title-asc">Name A-Z</SelectItem>
                <SelectItem value="title-desc">Name Z-A</SelectItem>
                <SelectItem value="duration-desc">Longest First</SelectItem>
                <SelectItem value="duration-asc">Shortest First</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                variant={viewMode === "grid" ? "default" : "outline"}
                size="icon"
                onClick={() => handleViewModeChange("grid")}
                title="Grid view"
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "outline"}
                size="icon"
                onClick={() => handleViewModeChange("list")}
                title="List view"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Processing Queue */}
        <div className="mt-8">
          <ProcessingQueue />
        </div>

        {/* Video List/Grid */}
        <div className="mt-8">
          {isLoading ? (
            viewMode === "grid" ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <VideoCardSkeleton key={i} />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Card key={i}>
                    <CardContent className="flex items-center gap-4 p-4">
                      <Skeleton className="h-20 w-32 rounded" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                        <div className="flex gap-2">
                          <Skeleton className="h-4 w-16" />
                          <Skeleton className="h-4 w-20" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )
          ) : videos.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-lg font-medium text-muted-foreground">
                No videos found
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                {searchQuery || statusFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Upload your first video to get started"}
              </p>
            </div>
          ) : viewMode === "grid" ? (
            <VideoGrid
              videos={videos}
              onDelete={handleDeleteClick}
              onEdit={handleEdit}
            />
          ) : (
            <VideoList
              videos={videos}
              onDelete={handleDeleteClick}
              onEdit={handleEdit}
            />
          )}
        </div>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Video</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this video? This action cannot
                be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setDeleteDialogOpen(false);
                  setVideoToDelete(null);
                }}
              >
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeleteConfirm}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}
