import { formatINR } from '@/lib/format';

interface HeroAmountProps {
  amount: number;
  label?: string;
  sublabel?: string;
}

export function HeroAmount({ amount, label, sublabel }: HeroAmountProps) {
  return (
    <div className="rounded-2xl border-2 border-emerald-600/30 bg-emerald-50/60 p-5 text-center">
      {label && (
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-900">
          {label}
        </p>
      )}
      <p className="mt-1 text-4xl sm:text-5xl font-extrabold tracking-tight text-emerald-950">
        {formatINR(amount)}
      </p>
      {sublabel && (
        <p className="mt-1 text-sm font-medium text-emerald-800">{sublabel}</p>
      )}
    </div>
  );
}
