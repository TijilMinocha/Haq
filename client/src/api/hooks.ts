import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { clearOperatorSession, getOperatorToken, setOperatorSession } from '@/lib/authStore';
import { saveCase } from '@/lib/caseStore';

import { api, unwrap } from './client';
import type {
  CaseCreate,
  CaseResume,
  CaseUpdate,
  CaseView,
  DocumentKind,
  DocumentPatch,
  LoginRequest,
} from './types';

export const queryKeys = {
  case: (id: string) => ['case', id] as const,
  schemes: ['schemes'] as const,
  scenarios: ['demo', 'scenarios'] as const,
  me: ['auth', 'me'] as const,
  operatorCases: (filters: OperatorCaseFilters) => ['operator', 'cases', filters] as const,
};

export interface OperatorCaseFilters {
  status?: string;
  q?: string;
}

// Mutations return the full CaseView; writing it to the cache avoids a second round trip.
function storeCase(client: QueryClient, view: CaseView): void {
  client.setQueryData(queryKeys.case(view.id), view);
}

export function useCase(caseId: string) {
  return useQuery({
    queryKey: queryKeys.case(caseId),
    queryFn: () =>
      unwrap(api.GET('/api/v1/cases/{case_id}', { params: { path: { case_id: caseId } } })),
  });
}

export function useCreateCase() {
  return useMutation({
    mutationFn: (body: CaseCreate) => unwrap(api.POST('/api/v1/cases', { body })),
    onSuccess: (created) => saveCase(created.case_id, created.case_code, created.access_token),
  });
}

export function useResumeCase() {
  return useMutation({
    mutationFn: (body: CaseResume) => unwrap(api.POST('/api/v1/cases/resume', { body })),
    onSuccess: (resumed, body) => saveCase(resumed.case_id, body.case_code, resumed.access_token),
  });
}

export function useUpdateCase(caseId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: CaseUpdate) =>
      unwrap(api.PATCH('/api/v1/cases/{case_id}', { params: { path: { case_id: caseId } }, body })),
    onSuccess: (view) => storeCase(client, view),
  });
}

export interface UploadInput {
  kind: DocumentKind;
  file: File;
}

export function useUploadDocument(caseId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, file }: UploadInput) =>
      unwrap(
        api.POST('/api/v1/cases/{case_id}/documents', {
          params: { path: { case_id: caseId } },
          body: { kind, file: file as unknown as string },
          bodySerializer: (body) => {
            const form = new FormData();
            form.append('kind', body.kind);
            form.append('file', file);
            return form;
          },
        }),
      ),
    onSuccess: (view) => storeCase(client, view),
  });
}

export interface DocumentPatchInput {
  documentId: string;
  patch: DocumentPatch;
}

export function useUpdateDocument(caseId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ documentId, patch }: DocumentPatchInput) =>
      unwrap(
        api.PATCH('/api/v1/cases/{case_id}/documents/{document_id}', {
          params: { path: { case_id: caseId, document_id: documentId } },
          body: patch,
        }),
      ),
    onSuccess: (view) => storeCase(client, view),
  });
}

export function useDeleteDocument(caseId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) =>
      unwrap(
        api.DELETE('/api/v1/cases/{case_id}/documents/{document_id}', {
          params: { path: { case_id: caseId, document_id: documentId } },
        }),
      ),
    onSuccess: (view) => storeCase(client, view),
  });
}

export function useSchemes() {
  return useQuery({
    queryKey: queryKeys.schemes,
    queryFn: () => unwrap(api.GET('/api/v1/meta/schemes')),
    staleTime: Infinity,
  });
}

export function useDemoScenarios() {
  return useQuery({
    queryKey: queryKeys.scenarios,
    queryFn: () => unwrap(api.GET('/api/v1/demo/scenarios')),
    staleTime: Infinity,
  });
}

export function useStartDemo() {
  return useMutation({
    mutationFn: (scenarioId: string) =>
      unwrap(
        api.POST('/api/v1/demo/scenarios/{scenario_id}', {
          params: { path: { scenario_id: scenarioId } },
        }),
      ),
    onSuccess: (created) => saveCase(created.case_id, created.case_code, created.access_token),
  });
}

export function useLogin() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: LoginRequest) => unwrap(api.POST('/api/v1/auth/login', { body })),
    onSuccess: (res) => {
      setOperatorSession({
        token: res.access_token,
        name: res.operator.name,
        email: res.operator.email,
      });
      client.setQueryData(queryKeys.me, res.operator);
    },
  });
}

export function useLogout() {
  const client = useQueryClient();
  return () => {
    clearOperatorSession();
    client.removeQueries({ queryKey: ['operator'] });
    client.removeQueries({ queryKey: queryKeys.me });
  };
}

export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => unwrap(api.GET('/api/v1/auth/me')),
    enabled: getOperatorToken() !== undefined,
  });
}

export function useOperatorCases(filters: OperatorCaseFilters) {
  return useQuery({
    queryKey: queryKeys.operatorCases(filters),
    queryFn: () => unwrap(api.GET('/api/v1/operator/cases', { params: { query: filters } })),
    enabled: getOperatorToken() !== undefined,
  });
}
