'use client';

import { useState } from 'react';
import { Video, Music, Image, Type, Eye, EyeOff, Lock, Unlock, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import type { Track, TrackUpdate } from '@/types/advancedEditor';

interface TrackHeaderProps {
  track: Track;
  onUpdate: (updates: TrackUpdate) => void;
  onDelete: () => void;
}

const TRACK_TYPE_ICONS = {
  video: Video,
  audio: Music,
  image: Image,
  text: Type,
  overlay: Image,
};

const TRACK_TYPE_COLORS = {
  video: 'bg-blue-500/10 text-blue-500',
  audio: 'bg-green-500/10 text-green-500',
  image: 'bg-purple-500/10 text-purple-500',
  text: 'bg-yellow-500/10 text-yellow-500',
  overlay: 'bg-pink-500/10 text-pink-500',
};

export function TrackHeader({ track, onUpdate, onDelete }: TrackHeaderProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(track.name);

  const Icon = TRACK_TYPE_ICONS[track.track_type];
  const colorClass = TRACK_TYPE_COLORS[track.track_type];

  const handleNameSubmit = () => {
    if (editedName.trim() && editedName !== track.name) {
      onUpdate({ name: editedName.trim() });
    }
    setIsEditingName(false);
  };

  const handleNameBlur = () => {
    handleNameSubmit();
  };

  const handleNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNameSubmit();
    } else if (e.key === 'Escape') {
      setEditedName(track.name);
      setIsEditingName(false);
    }
  };

  const toggleLock = () => {
    onUpdate({ is_locked: !track.is_locked });
  };

  const toggleVisibility = () => {
    onUpdate({ is_visible: !track.is_visible });
  };

  const toggleMute = () => {
    onUpdate({ is_muted: !track.is_muted });
  };

  const handleVolumeChange = (value: number[]) => {
    onUpdate({ volume: value[0] });
  };

  const handleOpacityChange = (value: number[]) => {
    onUpdate({ opacity: value[0] });
  };

  const isAudioTrack = track.track_type === 'audio' || track.track_type === 'video';
  const isVisualTrack = track.track_type === 'video' || track.track_type === 'image' || track.track_type === 'overlay';

  return (
    <div className="flex items-center gap-2 p-3 border-r border-border bg-card min-w-[250px] max-w-[250px]">
      <div className={`p-2 rounded ${colorClass}`}>
        <Icon className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        {isEditingName ? (
          <Input
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            onBlur={handleNameBlur}
            onKeyDown={handleNameKeyDown}
            className="h-7 text-sm"
            autoFocus
          />
        ) : (
          <div
            className="text-sm font-medium truncate cursor-pointer hover:text-primary"
            onDoubleClick={() => setIsEditingName(true)}
            title={track.name}
          >
            {track.name}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1">
        {/* Lock button */}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={toggleLock}
          title={track.is_locked ? 'Unlock track' : 'Lock track'}
        >
          {track.is_locked ? (
            <Lock className="w-3.5 h-3.5 text-orange-500" />
          ) : (
            <Unlock className="w-3.5 h-3.5" />
          )}
        </Button>

        {/* Visibility button */}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={toggleVisibility}
          title={track.is_visible ? 'Hide track' : 'Show track'}
        >
          {track.is_visible ? (
            <Eye className="w-3.5 h-3.5" />
          ) : (
            <EyeOff className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </Button>

        {/* Mute button (audio tracks only) */}
        {isAudioTrack && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={toggleMute}
            title={track.is_muted ? 'Unmute track' : 'Mute track'}
          >
            {track.is_muted ? (
              <VolumeX className="w-3.5 h-3.5 text-red-500" />
            ) : (
              <Volume2 className="w-3.5 h-3.5" />
            )}
          </Button>
        )}
      </div>

      {/* Volume slider (audio tracks) */}
      {isAudioTrack && !track.is_muted && (
        <div className="flex items-center gap-2 w-20">
          <Slider
            value={[track.volume]}
            onValueChange={handleVolumeChange}
            min={0}
            max={2}
            step={0.1}
            className="w-full"
            title={`Volume: ${Math.round(track.volume * 100)}%`}
          />
        </div>
      )}

      {/* Opacity slider (visual tracks) */}
      {isVisualTrack && track.is_visible && (
        <div className="flex items-center gap-2 w-20">
          <Slider
            value={[track.opacity]}
            onValueChange={handleOpacityChange}
            min={0}
            max={1}
            step={0.05}
            className="w-full"
            title={`Opacity: ${Math.round(track.opacity * 100)}%`}
          />
        </div>
      )}
    </div>
  );
}
