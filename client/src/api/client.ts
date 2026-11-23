import createClient, { type Middleware } from 'openapi-fetch';

import { env } from '@/config/env';
import { clearOperatorSession, getOperatorToken } from '@/lib/authStore';
import { getCaseToken } from '@/lib/caseStore';

import { ApiError, toApiError } from './errors';
import type { paths } from './schema';

const CASE_PATH = /\/cases\/([^/]+)/;

export function authHeaders(url: string): Record<string, string> {
  const headers: Record<string, string> = {};
  const caseId = CASE_PATH.exec(
    new URL(url, env.apiOrigin || window.location.origin).pathname,
  )?.[1];
  const caseToken = caseId && caseId !== 'resume' ? getCaseToken(caseId) : undefined;
  if (caseToken) headers['X-Case-Token'] = caseToken;
  const operatorToken = getOperatorToken();
  if (operatorToken) headers.Authorization = `Bearer ${operatorToken}`;
  return headers;
}

const auth: Middleware = {
  onRequest({ request }) {
    for (const [name, value] of Object.entries(authHeaders(request.url))) {
      request.headers.set(name, value);
    }
    return request;
  },
  onResponse({ request, response }) {
    // A 401 while sending a JWT means the 12-hour session ended; the operator logs in again.
    if (response.status === 401 && request.headers.has('Authorization')) {
      clearOperatorSession();
    }
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: env.apiOrigin });
api.use(auth);

interface FetchResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

/** Turns an openapi-fetch result into data, or throws ApiError with the server's error shape. */
export async function unwrap<T>(call: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>;
  try {
    result = await call;
  } catch (e) {
    throw new ApiError('network_error', e instanceof Error ? e.message : 'Network error', 0);
  }
  if (result.error !== undefined || !result.response.ok) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data as T;
}
