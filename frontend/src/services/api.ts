import axios, { AxiosInstance } from 'axios';
import {
  BugReport,
  RCAResult,
  RecommendationResult,
  ProcessedInput,
  AnalysisResult,
  SimilarBug,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface AuthUser {
  id: number;
  email: string;
  is_active: boolean;
}

export interface HistoryRecordSummary {
  id: number;
  description: string;
  input_type: string;
  severity: string;
  status: string;
  created_at: string;
  has_bug_report: boolean;
  has_rca: boolean;
  has_recommendations: boolean;
}

export interface HistoryRecordDetail {
  id: number;
  description: string;
  input_type: string;
  environment: Record<string, string> | null;
  processed_input: ProcessedInput | null;
  bug_report: BugReport | null;
  root_cause_analysis: RCAResult | null;
  recommendations: RecommendationResult | null;
  similar_bugs: SimilarBug[] | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

interface RecommendEndpointResponse {
  success: boolean;
  message: string;
  data: {
    record_id?: number;
    processed_input: ProcessedInput;
    bug_report: BugReport;
    root_cause_analysis: RCAResult;
    similar_bugs?: SimilarBug[];
    recommendations: RecommendationResult;
  };
}

interface GuestAnalyzeResponse {
  success: boolean;
  message: string;
  guest_mode: boolean;
  data: {
    processed_input: ProcessedInput;
    bug_report: BugReport;
    root_cause_analysis: RCAResult;
    similar_bugs?: SimilarBug[];
    recommendations: RecommendationResult;
  };
}

interface HistoryResponse {
  success: boolean;
  count: number;
  total_count: number;
  offset: number;
  limit: number;
  records: HistoryRecordSummary[];
}

interface HistoryRecordResponse {
  success: boolean;
  record: HistoryRecordDetail;
}

class BugReportApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  getToken(): string | null {
    return localStorage.getItem('bugreport_token');
  }

  setToken(token: string): void {
    localStorage.setItem('bugreport_token', token);
  }

  clearToken(): void {
    localStorage.removeItem('bugreport_token');
  }

  async register(input: { email: string; password: string }): Promise<AuthUser> {
    const response = await this.client.post<AuthUser>('/auth/register', input);
    return response.data;
  }

  async login(input: { email: string; password: string }): Promise<AuthTokenResponse> {
    const response = await this.client.post<AuthTokenResponse>('/auth/login', input);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<AuthUser> {
    const response = await this.client.get<AuthUser>('/auth/me');
    return response.data;
  }

  private normalizeRca(rca: RCAResult | (RCAResult & { root_causes?: RCAResult['probable_causes'] })): RCAResult {
    const probableCauses =
      rca?.probable_causes ??
      (rca as { root_causes?: RCAResult['probable_causes'] })?.root_causes ??
      [];

    return {
      ...rca,
      probable_causes: probableCauses,
    };
  }

  async analyzeError(input: {
    description: string;
    input_type: 'text' | 'stack_trace' | 'log' | 'json';
    environment?: Record<string, string>;
  }): Promise<AnalysisResult> {
    const preferredModel = localStorage.getItem('bugreport_preferred_model') || undefined;
    const recommendationResponse = await this.client.post<RecommendEndpointResponse>('/recommend-fix', {
      description: input.description,
      input_type: input.input_type,
      environment: input.environment || {},
      model: preferredModel,
      use_search: true,
    });

    return {
      ...recommendationResponse.data.data,
      record_id: recommendationResponse.data.data.record_id,
      root_cause_analysis: this.normalizeRca(recommendationResponse.data.data.root_cause_analysis),
      recommendations: recommendationResponse.data.data.recommendations,
      similar_bugs: recommendationResponse.data.data.similar_bugs || [],
    };
  }

  async analyzeErrorFree(input: {
    description: string;
    input_type: 'text' | 'stack_trace' | 'log' | 'json';
    environment?: Record<string, string>;
  }): Promise<AnalysisResult> {
    const preferredModel = localStorage.getItem('bugreport_preferred_model') || undefined;
    const response = await this.client.post<GuestAnalyzeResponse>('/analyze-free', {
      description: input.description,
      input_type: input.input_type,
      environment: input.environment || {},
      model: preferredModel,
      use_search: true,
    });

    return {
      ...response.data.data,
      root_cause_analysis: this.normalizeRca(response.data.data.root_cause_analysis),
      recommendations: response.data.data.recommendations,
      similar_bugs: response.data.data.similar_bugs || [],
    };
  }

  async getSupportedLanguages(): Promise<string[]> {
    const response = await this.client.get<{ languages: string[] }>('/supported-languages');
    return response.data.languages;
  }

  async getAvailableModels(): Promise<string[]> {
    const response = await this.client.get<{ available_models: string[] }>('/models');
    return response.data.available_models;
  }

  async getStats(): Promise<Record<string, unknown>> {
    const response = await this.client.get<Record<string, unknown>>('/stats');
    return response.data;
  }

  async getHealth(): Promise<Record<string, unknown>> {
    const response = await this.client.get<Record<string, unknown>>('/health');
    return response.data;
  }

  async getInfrastructureHealth(): Promise<Record<string, unknown>> {
    try {
      const response = await this.client.get<Record<string, unknown>>('/health');
      return response.data;
    } catch {
      const response = await axios.get<Record<string, unknown>>('/api/health');
      return response.data;
    }
  }

  async getHistory(page: number = 1, pageSize: number = 20): Promise<{
    records: HistoryRecordSummary[];
    totalCount: number;
  }> {
    const offset = Math.max(0, (page - 1) * pageSize);
    try {
      const response = await this.client.get<HistoryResponse>('/history', {
        params: { limit: pageSize, offset },
      });
      return {
        records: response.data.records || [],
        totalCount: response.data.total_count || 0,
      };
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw new Error('Sign in to view your saved analysis history.');
      }
      throw error;
    }
  }

  async getHistoryRecord(recordId: number): Promise<HistoryRecordDetail> {
    try {
      const response = await this.client.get<HistoryRecordResponse>(`/history/${recordId}`);
      return response.data.record;
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw new Error('Sign in to open history details.');
      }
      throw error;
    }
  }

  async deleteHistoryRecord(recordId: number): Promise<void> {
    try {
      await this.client.delete(`/history/${recordId}`);
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw new Error('Sign in to delete saved history records.');
      }
      throw error;
    }
  }
}

export const apiService = new BugReportApiService();
export type { BugReport, RCAResult, RecommendationResult, ProcessedInput, AnalysisResult };
