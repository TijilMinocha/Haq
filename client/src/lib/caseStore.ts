import { readJson, writeJson } from './storage';

const KEY = 'haq.cases';

export interface SavedCase {
  caseId: string;
  code: string;
  token: string;
  savedAt: string;
}

type CaseMap = Record<string, SavedCase>;

const load = (): CaseMap => readJson<CaseMap>(KEY, {});

export function saveCase(caseId: string, code: string, token: string): void {
  writeJson(KEY, {
    ...load(),
    [caseId]: { caseId, code, token, savedAt: new Date().toISOString() },
  });
}

export function saveCaseToken(caseId: string, token: string): void {
  const existing = load()[caseId];
  saveCase(caseId, existing?.code ?? '', token);
}

export function getCaseToken(caseId: string): string | undefined {
  return load()[caseId]?.token;
}

export function getSavedCase(caseId: string): SavedCase | undefined {
  return load()[caseId];
}

export function listSavedCases(): SavedCase[] {
  return Object.values(load()).sort((a, b) => b.savedAt.localeCompare(a.savedAt));
}

export function forgetCase(caseId: string): void {
  writeJson(KEY, Object.fromEntries(Object.entries(load()).filter(([id]) => id !== caseId)));
}
