/** Timeline types. */

export interface WaveformData {
  peaks: number[];
  duration: number;
  sample_rate: number;
}

export type WaveformStatusType = "processing" | "completed" | "failed";

export interface WaveformStatus {
  status: WaveformStatusType;
  progress?: number;
}

export interface Segment {
  id: string;
  start_time: number;
  end_time: number;
  selected: boolean;
}

export interface SegmentCreate {
  id: string;
  start_time: number;
  end_time: number;
  selected: boolean;
}
