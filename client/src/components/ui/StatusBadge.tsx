import { useTranslation } from 'react-i18next';

export type CoverStatus =
  | 'eligible'
  | 'likely_eligible'
  | 'needs_verification'
  | 'lapsed'
  | 'ineligible'
  | 'not_found';

interface StatusBadgeProps {
  status: CoverStatus;
}

const statusConfig: Record<
  CoverStatus,
  { bg: string; text: string; border: string; icon: string }
> = {
  eligible: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-800',
    border: 'border-emerald-300',
    icon: '✓',
  },
  likely_eligible: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-300',
    icon: '⏳',
  },
  needs_verification: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-300',
    icon: '🏦',
  },
  lapsed: {
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-300',
    icon: '⚠',
  },
  ineligible: {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-300',
    icon: '✕',
  },
  not_found: {
    bg: 'bg-slate-100',
    text: 'text-slate-600',
    border: 'border-slate-200',
    icon: '—',
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation();
  const cfg = statusConfig[status] ?? statusConfig.not_found;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}
    >
      <span aria-hidden="true">{cfg.icon}</span>
      <span>{t(`cover_status.${status}`)}</span>
    </span>
  );
}
