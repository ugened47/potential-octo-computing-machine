"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Video, HardDrive, Clock, Activity } from "lucide-react";
import type { DashboardStats } from "@/types/video";

interface StatsCardsProps {
  stats: DashboardStats;
}

export function StatsCards({ stats }: StatsCardsProps) {
  const statItems = [
    {
      title: "Total Videos",
      value: stats.total_videos.toString(),
      icon: Video,
      description: "All videos",
    },
    {
      title: "Storage Used",
      value: `${stats.storage_used_gb.toFixed(2)} GB`,
      icon: HardDrive,
      description: "Total storage",
    },
    {
      title: "Processing Time",
      value: `${stats.processing_time_minutes} min`,
      icon: Clock,
      description: "Total minutes",
    },
    {
      title: "Recent Activity",
      value: stats.recent_activity_count.toString(),
      icon: Activity,
      description: "Last 7 days",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statItems.map((item) => {
        const Icon = item.icon;
        return (
          <Card key={item.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {item.title}
              </CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{item.value}</div>
              <p className="text-xs text-muted-foreground">
                {item.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
