export interface RAGContextHit {
  id: string;
  text: string;
  raw_data: Record<string, unknown>;
  similarity_distance?: number;
}

export interface DatasetProfile {
  active_file?: string;
  total_rows?: number;
  total_columns?: number;
  discovered_numeric_fields?: string[];
  discovered_categorical_fields?: string[];
  numerical_distribution_profiles?: Record<string, Record<string, number>>;
}

export interface FilteredQueryOutput {
  query_executed?: string;
  matches_discovered?: number;
  data_slice?: Array<Record<string, unknown>>;
  error?: string;
  message?: string;
}

export interface Message {
  id: string;
  sender: 'user' | 'rei';
  text: string;
  timestamp: Date;
  routingMeta?: {
    trackSelected: string;
    reasoningTrace: string;
    appliedFilters: {
      column: string | null;
      operator: string | null;
      value: string | number | boolean | null;
    };
  };
  rawPayloads?: {
    ragContext: RAGContextHit[] | null;
    toolExecution: DatasetProfile | FilteredQueryOutput | Record<string, unknown> | null;
  };
}