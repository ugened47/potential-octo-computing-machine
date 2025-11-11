'use client';

import { useState, useRef, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import type { TrackItem, TrackItemUpdate } from '@/types/advancedEditor';

interface TimelineItemProps {
  item: TrackItem;
  scale: number; // pixels per second
  onUpdate: (updates: TrackItemUpdate) => void;
  onDelete: () => void;
  onSelect: () => void;
  isSelected: boolean;
}

const ITEM_TYPE_COLORS = {
  video_clip: 'bg-blue-500/80',
  audio_clip: 'bg-green-500/80',
  image: 'bg-purple-500/80',
  text: 'bg-yellow-500/80',
  shape: 'bg-pink-500/80',
};

export function TimelineItem({
  item,
  scale,
  onUpdate,
  onDelete,
  onSelect,
  isSelected,
}: TimelineItemProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState<'left' | 'right' | null>(null);
  const [dragStart, setDragStart] = useState({ x: 0, time: 0 });
  const itemRef = useRef<HTMLDivElement>(null);

  const left = item.start_time * scale;
  const width = item.duration * scale;
  const colorClass = ITEM_TYPE_COLORS[item.item_type];

  const hasError = !item.source_id && !item.source_url && item.item_type !== 'text';

  const handleMouseDown = (e: React.MouseEvent, action: 'drag' | 'resize-left' | 'resize-right') => {
    e.stopPropagation();
    onSelect();

    if (action === 'drag') {
      setIsDragging(true);
      setDragStart({ x: e.clientX, time: item.start_time });
    } else if (action === 'resize-left' || action === 'resize-right') {
      setIsResizing(action === 'resize-left' ? 'left' : 'right');
      setDragStart({ x: e.clientX, time: item.start_time });
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - dragStart.x;
        const deltaTime = deltaX / scale;
        const newStartTime = Math.max(0, dragStart.time + deltaTime);
        const newEndTime = newStartTime + item.duration;

        onUpdate({
          start_time: newStartTime,
          end_time: newEndTime,
        });
      } else if (isResizing) {
        const deltaX = e.clientX - dragStart.x;
        const deltaTime = deltaX / scale;

        if (isResizing === 'left') {
          const newStartTime = Math.max(0, Math.min(item.end_time - 0.1, dragStart.time + deltaTime));
          const newDuration = item.end_time - newStartTime;
          onUpdate({
            start_time: newStartTime,
            duration: newDuration,
            trim_start: item.trim_start + (newStartTime - item.start_time),
          });
        } else {
          const newDuration = Math.max(0.1, item.duration + deltaTime);
          const newEndTime = item.start_time + newDuration;
          onUpdate({
            end_time: newEndTime,
            duration: newDuration,
          });
        }
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(null);
    };

    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, dragStart, item, scale, onUpdate]);

  return (
    <div
      ref={itemRef}
      className={`absolute h-full ${colorClass} rounded border-2 ${
        isSelected ? 'border-primary' : 'border-transparent'
      } ${hasError ? 'border-red-500' : ''} ${isDragging ? 'opacity-70 cursor-move' : 'cursor-pointer'} overflow-hidden group transition-opacity`}
      style={{
        left: `${left}px`,
        width: `${width}px`,
      }}
      onMouseDown={(e) => handleMouseDown(e, 'drag')}
      onClick={onSelect}
      title={`${item.item_type}: ${formatTime(item.start_time)} - ${formatTime(item.end_time)} (${formatTime(item.duration)})`}
    >
      {/* Resize handle - left */}
      <div
        className="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize hover:bg-white/20 transition-colors"
        onMouseDown={(e) => handleMouseDown(e, 'resize-left')}
        title="Drag to trim start"
      />

      {/* Content */}
      <div className="px-2 py-1 flex items-center justify-between h-full">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-white truncate">
            {item.text_content || item.source_id || 'Untitled'}
          </div>
          {item.transition_in && (
            <div className="text-[10px] text-white/70">← Transition</div>
          )}
        </div>

        {hasError && (
          <AlertCircle className="w-4 h-4 text-red-300 flex-shrink-0 ml-1" />
        )}

        {item.transition_out && (
          <div className="text-[10px] text-white/70">→</div>
        )}
      </div>

      {/* Resize handle - right */}
      <div
        className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize hover:bg-white/20 transition-colors"
        onMouseDown={(e) => handleMouseDown(e, 'resize-right')}
        title="Drag to trim end"
      />
    </div>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
}
