import { beforeEach, describe, expect, it } from 'vitest';

import { forgetCase, getCaseToken, listSavedCases, saveCase } from './caseStore';

describe('caseStore', () => {
  beforeEach(() => localStorage.clear());

  it('saves, reads and forgets a case token', () => {
    saveCase('c_1', 'HAQ-7K3P', 'tok');
    expect(getCaseToken('c_1')).toBe('tok');
    expect(listSavedCases().map((c) => c.code)).toEqual(['HAQ-7K3P']);
    forgetCase('c_1');
    expect(getCaseToken('c_1')).toBeUndefined();
  });
});
