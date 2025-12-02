/**
 * Backend API Integration Service
 * Connects LoanAI frontend to the FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface UploadResponse {
  document_id: string;
  file_name: string;
  status: string;
  message?: string;
}

export interface DocumentMetadata {
  document_id: string;
  file_name: string;
  file_type?: string;
  file_size_bytes?: number;
  upload_timestamp?: string;
  processing_status?: string;
  extracted_data?: any;
  extracted_text?: string;
  accuracy?: number;
  accuracy_metrics?: {
    overall_accuracy?: number;
  };
}

export interface ExtractionResponse {
  document_id: string;
  extracted_data: any;
  accuracy_metrics?: {
    overall_accuracy: number;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  provider?: string;
  model?: string;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Upload a document to the backend
   */
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/v1/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Extract data from a document
   */
  async extractDocument(file: File): Promise<ExtractionResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/v1/extract`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Extraction failed' }));
      throw new Error(error.message || `Extraction failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List all documents available on the backend
   */
  async listDocuments(): Promise<DocumentMetadata[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/documents`);

    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.statusText}`);
    }

    const data = await response.json();
    return data.documents || [];
  }

  /**
   * Get document metadata
   */
  async getDocument(documentId: string): Promise<DocumentMetadata> {
    const response = await fetch(`${this.baseUrl}/api/v1/documents/${documentId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch document: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Send a chat message to the backend chatbot
   */
  async sendChatMessage(
    question: string,
    documentId: string,
    structuredData?: any,
    useMemory: boolean = true
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/advanced/chatbot/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
        structured_data: structuredData,
        use_memory: useMemory,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Chat failed' }));
      throw new Error(error.detail || error.message || `Chat failed: ${response.statusText}`);
    }

    const data = await response.json();
    // Extract the response text from the backend response structure
    if (data.success && data.response) {
      return {
        response: data.response.answer || data.response.text || JSON.stringify(data.response),
        provider: 'backend',
        model: 'rag-chatbot',
      };
    }
    return {
      response: JSON.stringify(data),
      provider: 'backend',
    };
  }

  /**
   * Get document extracted data
   */
  async getDocumentExtractedData(documentId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/documents/${documentId}/extracted-data`);

    if (!response.ok) {
      throw new Error(`Failed to fetch extracted data: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get document text content (for display)
   */
  async getDocumentContent(documentId: string): Promise<string> {
    try {
      // First try to get extracted data
      const extractedData = await this.getDocumentExtractedData(documentId);
      // Return formatted text from extracted data
      if (extractedData.extracted_text) {
        return extractedData.extracted_text;
      }
      // Fallback: return JSON stringified data
      return JSON.stringify(extractedData, null, 2);
    } catch (error) {
      // If extracted data not available, get metadata
      const metadata = await this.getDocument(documentId);
      return metadata.extracted_data ? JSON.stringify(metadata.extracted_data, null, 2) : '';
    }
  }

  /**
   * Get available LLM providers
   */
  async getProviders(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/providers`);

    if (!response.ok) {
      return []; // Return empty array if endpoint doesn't exist
    }

    const data = await response.json();
    return data.providers || [];
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }

    return response.json();
  }

  /**
   * Query loans
   */
  async queryLoans(query?: string): Promise<any[]> {
    const url = query 
      ? `${this.baseUrl}/api/v1/loans?query=${encodeURIComponent(query)}`
      : `${this.baseUrl}/api/v1/loans`;

    const response = await fetch(url);

    if (!response.ok) {
      return []; // Return empty array if endpoint doesn't exist
    }

    return response.json();
  }

  /**
   * Compare loans
   */
  async compareLoans(loanIds: string[]): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loanIds),
    });

    if (!response.ok) {
      throw new Error(`Comparison failed: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new ApiService();
export default apiService;

