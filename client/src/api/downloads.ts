import { env } from '@/config/env';

import { authHeaders } from './client';
import { ApiError, toApiError } from './errors';
import type { Scheme } from './types';

async function download(path: string, fallbackName: string): Promise<void> {
  const url = `${env.apiOrigin}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { headers: authHeaders(url) });
  } catch (e) {
    throw new ApiError('network_error', e instanceof Error ? e.message : 'Network error', 0);
  }
  if (!response.ok) {
    throw toApiError(await response.json().catch(() => null), response.status);
  }
  const disposition = response.headers.get('Content-Disposition') ?? '';
  const name = /filename="([^"]+)"/.exec(disposition)?.[1] ?? fallbackName;
  const href = URL.createObjectURL(await response.blob());
  const a = document.createElement('a');
  a.href = href;
  a.download = name;
  a.click();
  URL.revokeObjectURL(href);
}

export function downloadForm(caseId: string, scheme: Scheme): Promise<void> {
  return download(`/api/v1/cases/${caseId}/forms/${scheme}`, `${scheme}-claim.pdf`);
}

export function downloadEscalation(caseId: string, scheme: Scheme): Promise<void> {
  return download(
    `/api/v1/cases/${caseId}/letters/escalation?scheme=${scheme}`,
    `${scheme}-escalation.pdf`,
  );
}
