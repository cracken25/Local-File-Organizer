import { DocumentItem, Taxonomy } from '../types';

const BASE_URL = '/api';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Scan directory
  async scan(data: { input_path: string; output_path?: string }) {
    return this.request('/scan', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Start classification
  async classify(data: { mode: string }) {
    return this.request('/classify', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Get classification status
  async getClassifyStatus(): Promise<{ is_classifying: boolean; progress: number }> {
    return this.request('/classify/status');
  }

  // Get items
  async getItems(params?: {
    status?: string;
    workspace?: string;
    min_confidence?: number;
  }): Promise<DocumentItem[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.workspace) query.append('workspace', params.workspace);
    if (params?.min_confidence !== undefined) {
      query.append('min_confidence', params.min_confidence.toString());
    }

    const queryString = query.toString();
    return this.request(`/items${queryString ? `?${queryString}` : ''}`);
  }

  // Get single item
  async getItem(id: string): Promise<DocumentItem> {
    return this.request(`/items/${id}`);
  }

  // Update item
  async updateItem(id: string, data: Partial<DocumentItem>): Promise<DocumentItem> {
    return this.request(`/items/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Bulk action
  async bulkAction(data: {
    item_ids: string[];
    action: string;
    workspace?: string;
  }): Promise<{ updated: number }> {
    return this.request('/items/bulk-action', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Migrate files
  async migrate(data?: { dry_run?: boolean }): Promise<{ migrated: number }> {
    return this.request('/migrate', {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  }

  // Get taxonomy
  async getTaxonomy(): Promise<Taxonomy> {
    return this.request('/taxonomy');
  }

  // Get statistics
  async getStatistics(): Promise<any> {
    return this.request('/statistics');
  }

  // Browse folder
  async browseFolder(title: string = 'Select Folder'): Promise<{ path: string | null; success: boolean; error?: string }> {
    return this.request('/browse/folder', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  // Get saved paths
  async getSavedPaths(): Promise<{ input_path: string; output_path: string; mode: string }> {
    return this.request('/config/paths');
  }

  // Save paths
  async savePaths(data: { input_path?: string; output_path?: string; mode?: string }): Promise<{ success: boolean }> {
    return this.request('/config/paths', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Clear session
  async clearSession(): Promise<{ message: string }> {
    return this.request('/session', {
      method: 'DELETE',
    });
  }
}

export const apiClient = new APIClient();

