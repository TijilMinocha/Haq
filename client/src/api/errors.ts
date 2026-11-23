export type ApiErrorCode =
  | 'validation_error'
  | 'invalid_token'
  | 'invalid_credentials'
  | 'forbidden'
  | 'too_many_attempts'
  | 'case_not_found'
  | 'document_not_found'
  | 'scenario_not_found'
  | 'unsupported_file'
  | 'file_too_large'
  | 'document_unreadable'
  | 'form_not_applicable'
  | 'extractor_unavailable'
  | 'network_error'
  | 'unknown_error';

export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(
    code: ApiErrorCode,
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

interface ErrorBody {
  error?: { code?: string; message?: string; details?: Record<string, unknown> };
}

export function toApiError(body: unknown, status: number): ApiError {
  const err = (body as ErrorBody | null)?.error;
  return new ApiError(
    (err?.code as ApiErrorCode | undefined) ?? 'unknown_error',
    err?.message ?? `Request failed (${status})`,
    status,
    err?.details ?? {},
  );
}

export function isApiError(e: unknown, code?: ApiErrorCode): e is ApiError {
  return e instanceof ApiError && (code === undefined || e.code === code);
}
