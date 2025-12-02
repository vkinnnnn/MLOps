
export enum ViewMode {
  TALK_TO_DOCS = 'TALK_TO_DOCS',
  UPLOAD = 'UPLOAD',
  COPILOT = 'COPILOT'
}

export interface DocumentFile {
  id: string;
  name: string;
  type: string;
  size: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  content?: string; // Extracted content from backend
  uploadDate: string;
  accuracy?: number; // From Lab3 extractor
  documentId?: string; // Backend document ID
  extractedData?: any; // Structured extracted data from backend
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
}

export interface AudioVisualizerProps {
  isRecording: boolean;
  volume: number;
}
