export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  file_name: string;
  chunk_id: number;
  content_preview: string;
}

export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  upload_time: Date;
  trace_id: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
}

export interface QueryStatus {
  status: 'processing' | 'completed' | 'error' | 'not_found';
  result?: {
    response: string;
    sources: Source[];
    query: string;
  };
  error?: string;
}