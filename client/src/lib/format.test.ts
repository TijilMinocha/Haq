import type { TFunction } from 'i18next';
import { describe, expect, it } from 'vitest';

import { daysLeftLabel, formatDate, formatINR } from './format';

describe('formatINR', () => {
  it('uses Indian digit grouping', () => {
    expect(formatINR(600000)).toBe('₹6,00,000');
  });
});

describe('formatDate', () => {
  it('keeps the calendar date', () => {
    expect(formatDate('2026-12-15', 'en')).toBe('15 December 2026');
  });
});

describe('daysLeftLabel', () => {
  const t = ((key: string, opts?: { count?: number }) =>
    `${key}:${opts?.count ?? ''}`) as unknown as TFunction;

  it('handles future, today and past', () => {
    expect(daysLeftLabel(5, t)).toBe('deadline.days_left:5');
    expect(daysLeftLabel(0, t)).toBe('deadline.today:');
    expect(daysLeftLabel(-3, t)).toBe('deadline.passed:3');
  });
});
