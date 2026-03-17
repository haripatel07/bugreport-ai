import axios, { AxiosInstance } from 'axios';
import {
  BugReport,
  RCAResult,
  RecommendationResult,
  ProcessedInput,
  AnalysisResult,
  SimilarBug,
} from '../types';

const API_BASE = '/api';

class BugReportApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async analyzeError(input: {
    error_input: string;
    input_type: 'text' | 'stack_trace' | 'log' | 'json';
    environment?: Record<string, string>;
  }): Promise<AnalysisResult> {
    const response = await this.client.post<AnalysisResult>('/recommend-fix', {
      error_input: input.error_input,
      input_type: input.input_type,
      environment: input.environment || {},
      use_search: true,
    });
    return response.data;
  }

  async searchSimilarBugs(query: string, k: number = 5): Promise<SimilarBug[]> {
    const response = await this.client.post<{ results: SimilarBug[] }>('/search/similar', {
      query,
      k,
      min_score: 0.3,
    });
    return response.data.results;
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
}

export const apiService = new BugReportApiService();
export type { BugReport, RCAResult, RecommendationResult, ProcessedInput, AnalysisResult, SimilarBug };
