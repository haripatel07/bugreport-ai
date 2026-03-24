import axios, { AxiosInstance } from 'axios';
import {
  BugReport,
  RCAResult,
  Recommendation,
  RecommendationResult,
  ProcessedInput,
  AnalysisResult,
} from '../types';

const API_BASE = '/api';

interface AnalyzeEndpointResponse {
  success: boolean;
  message: string;
  data: {
    processed_input: ProcessedInput;
    bug_report: BugReport;
    root_cause_analysis: RCAResult;
  };
}

interface RecommendEndpointResponse {
  success: boolean;
  message: string;
  data: {
    processed_input: ProcessedInput;
    root_cause_analysis: RCAResult;
    recommendations: RecommendationResult | {
      recommendations: Array<Recommendation | {
        fix?: string;
        code?: string;
        difficulty?: string;
        reason?: string;
      }>;
      recommendation_source?: string;
      generation_time_ms?: number;
      context_used?: string[];
      similar_bugs_consulted?: number;
      rca_causes_consulted?: number;
    };
  };
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

  private normalizeRecommendations(
    recommendationResult: RecommendEndpointResponse['data']['recommendations']
  ): RecommendationResult {
    const recommendations = (recommendationResult?.recommendations ?? []).map((item, idx): Recommendation => {
      const candidate = item as Recommendation & {
        fix?: string;
        code?: string;
        reason?: string;
      };

      if (candidate.title || candidate.description || candidate.implementation_steps) {
        return {
          title: candidate.title || `Recommendation ${idx + 1}`,
          description: candidate.description || candidate.reason || 'Suggested fix from analysis pipeline.',
          difficulty: candidate.difficulty || 'medium',
          implementation_steps: candidate.implementation_steps || [],
          code_example: candidate.code_example,
        };
      }

      return {
        title: `Recommendation ${idx + 1}`,
        description: candidate.fix || candidate.reason || 'Suggested fix from analysis pipeline.',
        difficulty: candidate.difficulty || 'medium',
        implementation_steps: candidate.fix ? [candidate.fix] : [],
        code_example: candidate.code,
      };
    });

    return {
      recommendations,
      recommendation_source: recommendationResult?.recommendation_source || 'unknown',
      generation_time_ms: recommendationResult?.generation_time_ms || 0,
    };
  }

  async analyzeError(input: {
    description: string;
    input_type: 'text' | 'stack_trace' | 'log' | 'json';
    environment?: Record<string, string>;
  }): Promise<AnalysisResult> {
    const [analysisResponse, recommendationResponse] = await Promise.all([
      this.client.post<AnalyzeEndpointResponse>('/analyze', {
        description: input.description,
        input_type: input.input_type,
        environment: input.environment || {},
      }),
      this.client.post<RecommendEndpointResponse>('/recommend-fix', {
        description: input.description,
        input_type: input.input_type,
        environment: input.environment || {},
        use_search: false,
      }),
    ]);

    return {
      ...analysisResponse.data.data,
      root_cause_analysis: this.normalizeRca(analysisResponse.data.data.root_cause_analysis),
      recommendations: this.normalizeRecommendations(recommendationResponse.data.data.recommendations),
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
}

export const apiService = new BugReportApiService();
export type { BugReport, RCAResult, RecommendationResult, ProcessedInput, AnalysisResult };
