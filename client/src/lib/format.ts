import type { TFunction } from 'i18next';

const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

/** Indian digit grouping: 600000 -> ₹6,00,000. */
export function formatINR(rupees: number): string {
  return inr.format(rupees);
}

export function formatDate(iso: string, language: string): string {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return iso;
  // Construct in UTC so the calendar date never shifts with the device timezone.
  const date = new Date(Date.UTC(y, m - 1, d));
  return new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}

export function daysLeftLabel(daysLeft: number, t: TFunction): string {
  if (daysLeft < 0) return t('deadline.passed', { count: -daysLeft });
  if (daysLeft === 0) return t('deadline.today');
  return t('deadline.days_left', { count: daysLeft });
}
