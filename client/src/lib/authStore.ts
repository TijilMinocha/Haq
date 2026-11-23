import { readJson, remove, writeJson } from './storage';

const KEY = 'haq.operator';

export interface OperatorSession {
  token: string;
  name: string;
  email: string;
}

type Listener = () => void;
const listeners = new Set<Listener>();

export function getOperatorSession(): OperatorSession | null {
  return readJson<OperatorSession | null>(KEY, null);
}

export function getOperatorToken(): string | undefined {
  return getOperatorSession()?.token;
}

export function isOperator(): boolean {
  return getOperatorToken() !== undefined;
}

export function setOperatorSession(session: OperatorSession): void {
  writeJson(KEY, session);
  listeners.forEach((l) => l());
}

export function clearOperatorSession(): void {
  remove(KEY);
  listeners.forEach((l) => l());
}

/** For useSyncExternalStore, so screens re-render on login and logout. */
export function subscribeOperator(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
