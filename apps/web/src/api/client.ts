/*
 * The only place the web app talks to the backend.
 *
 * Every call is a relative `/api/v1/...` path so the same code works behind the
 * Vite dev proxy (in Docker `/api` -> http://api:8000) and behind whatever
 * reverse proxy fronts a production build. No host is ever hardcoded.
 *
 * The API's error envelope `{ error: { code, message, details } }` is unwrapped
 * into `ApiError`; transport failures become `ApiConnectionError`. Callers (and
 * TanStack Query) can branch on those without re-parsing responses.
 */

import type {
  ContentDetail,
  ContentSummary,
  ErrorCode,
  ExerciseSubmissionRequest,
  HealthResponse,
  LessonCompletionResponse,
  LessonDetail,
  OllamaReview,
  PathDetail,
  PathEnrollmentResponse,
  PathSummary,
  PlanItem,
  PlaygroundRunRequest,
  ProgressSummary,
  PublicRunRequest,
  QuizAnswerRequest,
  QuizAnswerResponse,
  QuizDetail,
  ReviewRequest,
  RunResult,
  SubmissionResponse,
} from '../contracts';

export const API_BASE = '/api/v1';

export class ApiConnectionError extends Error {
  constructor(message = 'The API could not be reached.') {
    super(message);
    this.name = 'ApiConnectionError';
  }
}

export class ApiError extends Error {
  readonly code: ErrorCode | 'unknown';
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(
    code: ErrorCode | 'unknown',
    message: string,
    status: number,
    details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

type Query = Record<string, string | number | undefined>;

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  query?: Query;
  signal?: AbortSignal;
}

function buildPath(path: string, query?: Query): string {
  const url = `${API_BASE}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

function looksLikeEnvelope(
  data: unknown,
): data is { error: { code: string; message: string; details?: Record<string, unknown> } } {
  return (
    typeof data === 'object' &&
    data !== null &&
    'error' in data &&
    typeof (data as { error: unknown }).error === 'object' &&
    (data as { error: unknown }).error !== null
  );
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, signal } = options;

  let response: Response;
  try {
    response = await fetch(buildPath(path, query), {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause;
    throw new ApiConnectionError();
  }

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      if (!response.ok) {
        throw new ApiError('unknown', text || response.statusText, response.status);
      }
      throw new ApiError('unknown', 'The API returned a non-JSON response.', response.status);
    }
  }

  if (!response.ok) {
    if (looksLikeEnvelope(payload)) {
      const { code, message, details } = payload.error;
      throw new ApiError(
        (code as ErrorCode) ?? 'unknown',
        message ?? response.statusText,
        response.status,
        details ?? {},
      );
    }
    throw new ApiError('unknown', response.statusText || 'Request failed.', response.status);
  }

  return payload as T;
}

export const apiClient = {
  health(signal?: AbortSignal): Promise<HealthResponse> {
    return request<HealthResponse>('/health', { signal });
  },

  listContent(signal?: AbortSignal): Promise<ContentSummary[]> {
    return request<ContentSummary[]>('/content', { signal });
  },

  getContent(exerciseId: string, signal?: AbortSignal): Promise<ContentDetail> {
    return request<ContentDetail>(`/content/${encodeURIComponent(exerciseId)}`, { signal });
  },

  getLesson(lessonId: string, signal?: AbortSignal): Promise<LessonDetail> {
    return request<LessonDetail>(`/content/${encodeURIComponent(lessonId)}`, { signal });
  },

  getQuiz(quizId: string, signal?: AbortSignal): Promise<QuizDetail> {
    return request<QuizDetail>(`/content/${encodeURIComponent(quizId)}`, { signal });
  },

  completeLesson(lessonId: string, signal?: AbortSignal): Promise<LessonCompletionResponse> {
    return request<LessonCompletionResponse>(
      `/lessons/${encodeURIComponent(lessonId)}/complete`,
      { method: 'POST', signal },
    );
  },

  listPaths(signal?: AbortSignal): Promise<PathSummary[]> {
    return request<PathSummary[]>('/paths', { signal });
  },

  getPath(pathId: string, signal?: AbortSignal): Promise<PathDetail> {
    return request<PathDetail>(`/paths/${encodeURIComponent(pathId)}`, { signal });
  },

  enrollPath(pathId: string, signal?: AbortSignal): Promise<PathEnrollmentResponse> {
    return request<PathEnrollmentResponse>(`/paths/${encodeURIComponent(pathId)}/enroll`, {
      method: 'POST',
      signal,
    });
  },

  unenrollPath(pathId: string, signal?: AbortSignal): Promise<PathEnrollmentResponse> {
    return request<PathEnrollmentResponse>(`/paths/${encodeURIComponent(pathId)}/unenroll`, {
      method: 'POST',
      signal,
    });
  },

  getPlan(signal?: AbortSignal): Promise<PlanItem[]> {
    return request<PlanItem[]>('/plan', { signal });
  },

  getProgress(signal?: AbortSignal): Promise<ProgressSummary> {
    return request<ProgressSummary>('/progress', { signal });
  },

  runExercise(body: PublicRunRequest, signal?: AbortSignal): Promise<RunResult> {
    return request<RunResult>('/exercises/run', { method: 'POST', body, signal });
  },

  submitExercise(
    body: ExerciseSubmissionRequest,
    signal?: AbortSignal,
  ): Promise<SubmissionResponse> {
    return request<SubmissionResponse>('/exercises/submit', { method: 'POST', body, signal });
  },

  runPlayground(body: PlaygroundRunRequest, signal?: AbortSignal): Promise<RunResult> {
    return request<RunResult>('/runs', { method: 'POST', body, signal });
  },

  answerQuiz(body: QuizAnswerRequest, signal?: AbortSignal): Promise<QuizAnswerResponse> {
    return request<QuizAnswerResponse>('/quizzes/answer', { method: 'POST', body, signal });
  },

  requestReview(body: ReviewRequest, signal?: AbortSignal): Promise<OllamaReview> {
    return request<OllamaReview>('/reviews', { method: 'POST', body, signal });
  },
};

export type ApiClient = typeof apiClient;
