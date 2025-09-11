/**
 * 🚀 Cliente API Tipado
 * ====================
 * 
 * Cliente HTTP totalmente tipado usando os tipos auto-gerados.
 * Zero any types - Type safety completo.
 */

import type { paths } from '../types/api-generated';
import type { ApiResponse, PaginatedData } from '../types';

// Extrai tipos de operação do OpenAPI
type ApiOperations = paths;

// Helper para extrair tipos de resposta
type ExtractResponse<T> = T extends { responses: { 200: { content: { 'application/json': infer R } } } } 
  ? R 
  : never;

// Helper para extrair tipos de request body
type ExtractRequestBody<T> = T extends { requestBody: { content: { 'application/json': infer R } } } 
  ? R 
  : never;

// Helper para extrair parâmetros de path
type ExtractPathParams<T> = T extends { parameters: { path: infer P } } ? P : never;

// Helper para extrair query parameters
type ExtractQueryParams<T> = T extends { parameters: { query: infer Q } } ? Q : never;

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  onError?: (error: ApiError) => void;
}

export interface ApiError {
  message: string;
  status: number;
  statusText: string;
  details?: Record<string, unknown>;
}

export class TypedApiClient {
  private baseURL: string;
  private timeout: number;
  private headers: Record<string, string>;
  private onError?: (error: ApiError) => void;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, '');
    this.timeout = config.timeout || 10000;
    this.headers = {
      'Content-Type': 'application/json',
      ...config.headers
    };
    this.onError = config.onError;
  }

  /**
   * Método genérico para fazer requests tipados
   */
  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${path}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.headers,
          ...options.headers
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          message: errorData.message || response.statusText,
          status: response.status,
          statusText: response.statusText,
          details: errorData
        };
        
        this.onError?.(error);
        throw error;
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        const timeoutError: ApiError = {
          message: 'Request timeout',
          status: 408,
          statusText: 'Request Timeout'
        };
        this.onError?.(timeoutError);
        throw timeoutError;
      }
      
      throw error;
    }
  }

  /**
   * GET tipado
   */
  async get<
    Path extends keyof ApiOperations,
    Operation extends ApiOperations[Path] = ApiOperations[Path],
    GetOp extends Operation['get'] = Operation['get'],
    ResponseType = ExtractResponse<GetOp>,
    PathParams = ExtractPathParams<GetOp>,
    QueryParams = ExtractQueryParams<GetOp>
  >(
    path: Path,
    params?: {
      path?: PathParams;
      query?: QueryParams;
    }
  ): Promise<ResponseType> {
    let url = path as string;
    
    // Substituir parâmetros de path
    if (params?.path) {
      Object.entries(params.path).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, String(value));
      });
    }
    
    // Adicionar query parameters
    if (params?.query) {
      const searchParams = new URLSearchParams();
      Object.entries(params.query).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    return this.request<ResponseType>(url, { method: 'GET' });
  }

  /**
   * POST tipado
   */
  async post<
    Path extends keyof ApiOperations,
    Operation extends ApiOperations[Path] = ApiOperations[Path],
    PostOp extends Operation['post'] = Operation['post'],
    ResponseType = ExtractResponse<PostOp>,
    RequestBodyType = ExtractRequestBody<PostOp>,
    PathParams = ExtractPathParams<PostOp>
  >(
    path: Path,
    data?: RequestBodyType,
    params?: {
      path?: PathParams;
    }
  ): Promise<ResponseType> {
    let url = path as string;
    
    // Substituir parâmetros de path
    if (params?.path) {
      Object.entries(params.path).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, String(value));
      });
    }

    return this.request<ResponseType>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  /**
   * PUT tipado
   */
  async put<
    Path extends keyof ApiOperations,
    Operation extends ApiOperations[Path] = ApiOperations[Path],
    PutOp extends Operation['put'] = Operation['put'],
    ResponseType = ExtractResponse<PutOp>,
    RequestBodyType = ExtractRequestBody<PutOp>,
    PathParams = ExtractPathParams<PutOp>
  >(
    path: Path,
    data?: RequestBodyType,
    params?: {
      path?: PathParams;
    }
  ): Promise<ResponseType> {
    let url = path as string;
    
    if (params?.path) {
      Object.entries(params.path).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, String(value));
      });
    }

    return this.request<ResponseType>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  /**
   * DELETE tipado
   */
  async delete<
    Path extends keyof ApiOperations,
    Operation extends ApiOperations[Path] = ApiOperations[Path],
    DeleteOp extends Operation['delete'] = Operation['delete'],
    ResponseType = ExtractResponse<DeleteOp>,
    PathParams = ExtractPathParams<DeleteOp>
  >(
    path: Path,
    params?: {
      path?: PathParams;
    }
  ): Promise<ResponseType> {
    let url = path as string;
    
    if (params?.path) {
      Object.entries(params.path).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, String(value));
      });
    }

    return this.request<ResponseType>(url, { method: 'DELETE' });
  }

  /**
   * Configura token de autenticação
   */
  setAuthToken(token: string) {
    this.headers.Authorization = `Bearer ${token}`;
  }

  /**
   * Remove token de autenticação
   */
  clearAuth() {
    delete this.headers.Authorization;
  }
}

// Instância padrão do cliente
export const apiClient = new TypedApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://wppagent-production.up.railway.app',
  onError: (error) => {
    console.error('API Error:', error);
    // Aqui você pode adicionar notificações, logging, etc.
  }
});

export default apiClient;
