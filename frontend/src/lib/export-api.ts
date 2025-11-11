/** API client for video export operations. */

import { apiRequest } from "./api-client";
import type {
  Export,
  ExportCreateRequest,
  ExportDownloadResponse,
  ExportListResponse,
  ExportProgress,
} from "@/types/export";

/**
 * Create a new export job for a video.
 */
export async function createExport(
  videoId: string,
  config: ExportCreateRequest,
): Promise<Export> {
  return apiRequest<Export>(`/api/videos/${videoId}/exports`, {
    method: "POST",
    body: JSON.stringify(config),
  });
}

/**
 * Get export details by ID.
 */
export async function getExport(exportId: string): Promise<Export> {
  return apiRequest<Export>(`/api/exports/${exportId}`, {
    method: "GET",
  });
}

/**
 * Get real-time export progress.
 */
export async function getExportProgress(exportId: string): Promise<ExportProgress> {
  return apiRequest<ExportProgress>(`/api/exports/${exportId}/progress`, {
    method: "GET",
  });
}

/**
 * Get download URL for completed export.
 */
export async function getExportDownloadUrl(
  exportId: string,
): Promise<ExportDownloadResponse> {
  return apiRequest<ExportDownloadResponse>(`/api/exports/${exportId}/download`, {
    method: "GET",
  });
}

/**
 * Cancel in-progress export or delete completed export.
 */
export async function deleteExport(exportId: string): Promise<void> {
  return apiRequest<void>(`/api/exports/${exportId}`, {
    method: "DELETE",
  });
}

/**
 * List all exports for a video.
 */
export async function getVideoExports(
  videoId: string,
  params?: {
    page?: number;
    limit?: number;
    status?: string;
  },
): Promise<ExportListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", params.page.toString());
  if (params?.limit) queryParams.set("limit", params.limit.toString());
  if (params?.status) queryParams.set("status_filter", params.status);

  const queryString = queryParams.toString();
  const url = queryString
    ? `/api/videos/${videoId}/exports?${queryString}`
    : `/api/videos/${videoId}/exports`;

  return apiRequest<ExportListResponse>(url, {
    method: "GET",
  });
}

/**
 * Trigger browser download for completed export.
 */
export async function downloadExport(exportId: string): Promise<void> {
  const { url } = await getExportDownloadUrl(exportId);

  // Trigger browser download
  const link = document.createElement("a");
  link.href = url;
  link.download = ""; // Let browser determine filename from Content-Disposition
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Cancel an in-progress export.
 */
export async function cancelExport(exportId: string): Promise<void> {
  return deleteExport(exportId);
}

/**
 * Calculate estimated file size for export configuration.
 */
export function estimateExportSize(
  duration: number,
  resolution: string,
  quality: string,
): number {
  // Rough estimates in MB per minute
  const bitrateEstimates: Record<string, Record<string, number>> = {
    "720p": { high: 10, medium: 5, low: 2.5 },
    "1080p": { high: 20, medium: 10, low: 5 },
    "4k": { high: 50, medium: 25, low: 12 },
  };

  const mbPerMinute = bitrateEstimates[resolution]?.[quality] || 10;
  const durationMinutes = duration / 60;
  const estimatedMB = mbPerMinute * durationMinutes;

  return Math.round(estimatedMB * 1024 * 1024); // Convert to bytes
}
