// API Response Types
export interface ProcessedInput {
  language: string;
  error_type: string;
  error_message: string;
  file_path: string;
  line_number: number;
  stack_frames: StackFrame[];
  raw_text: string;
}

export interface StackFrame {
  function: string;
  file: string;
  line: number;
  code_context: string;
}

export interface BugReport {
  title: string;
  description: string;
  steps_to_reproduce: string[];
  expected_behavior: string;
  actual_behavior: string;
  severity: string;
  priority?: string;
  affected_components: string[];
  environment: Record<string, string>;
  root_cause?: string;
}

export interface RCAResult {
  error_type: string;
  confidence: number;
  probable_causes: ProbableCause[];
  severity: string;
}

export interface ProbableCause {
  cause: string;
  confidence: number;
  recommendation: string;
  code_example: string;
  evidence: string[];
}

export interface Recommendation {
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  implementation_steps: string[];
  code_example?: string | null;
}

export interface RecommendationResult {
  recommendations: Recommendation[];
  recommendation_source: string;
  generation_time_ms: number;
}

export interface SimilarBug {
  repository: string;
  title: string;
  similarity_pct: string;
  similarity_score?: number;
  number?: number;
  url?: string;
  body_snippet?: string;
}

export interface AnalysisResult {
  record_id?: number;
  processed_input: ProcessedInput;
  bug_report: BugReport;
  root_cause_analysis: RCAResult;
  recommendations?: RecommendationResult;
  similar_bugs?: SimilarBug[];
}

// Form Types
export interface AnalysisState {
  loading: boolean;
  result: AnalysisResult | null;
  error: string | null;
  currentTab: number;
}

export type InputType = 'text' | 'stack_trace' | 'log' | 'json';

export interface ErrorFormState {
  errorInput: string;
  inputType: InputType;
  environment: string;
  submitting: boolean;
}
