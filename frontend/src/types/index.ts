export interface DocumentItem {
  id: string;
  source_path: string;
  original_filename: string;
  extracted_text?: string;
  proposed_workspace: string;
  proposed_subpath: string;
  proposed_filename: string;
  confidence: number;
  status: string;
  description?: string;
  file_size?: number;
  file_extension?: string;
  migrated_path?: string;
  migrated_at?: string;
  sha256?: string;
  reviewer_notes?: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
}

export interface Taxonomy {
  workspaces: Workspace[];
}



