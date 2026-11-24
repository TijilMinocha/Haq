import { useEffect, useState } from 'react';
import { formatINR } from '@/lib/format';

interface HeroAmountProps {
  amount: number;
  label?: string;
  sublabel?: string;
}

export function HeroAmount({ amount, label, sublabel }: HeroAmountProps) {
  const [displayAmount, setDisplayAmount] = useState(() => (amount > 0 ? 0 : amount));

  useEffect(() => {
    if (amount <= 0) return;

    const duration = 750;
    const steps = 20;
    const stepDuration = duration / steps;
    const increment = amount / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= amount) {
        setDisplayAmount(amount);
        clearInterval(timer);
      } else {
        setDisplayAmount(Math.round(current));
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [amount]);

  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-emerald-700/40 bg-gradient-to-b from-emerald-50/90 via-emerald-50/50 to-white p-5 sm:p-6 text-center shadow-xs">
      {/* Subtle guilloché security background pattern */}
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.06] text-emerald-950"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <path
          d="M0 20 Q 25 5, 50 20 T 100 20 M0 40 Q 25 25, 50 40 T 100 40 M0 60 Q 25 45, 50 60 T 100 60 M0 80 Q 25 65, 50 80 T 100 80"
          stroke="currentColor"
          strokeWidth="0.8"
        />
      </svg>

      {/* Official Government Scheme entitlement badge */}
      <div className="relative z-10 flex items-center justify-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-emerald-900 bg-emerald-100/70 py-1 px-3 rounded-full mx-auto w-fit border border-emerald-300/60 mb-2">
        <span aria-hidden="true">🏛️</span>
        <span>{label || 'TOTAL CLAIMABLE AMOUNT'}</span>
      </div>

      {/* Hero Rupee Amount with Tabular Digits */}
      <div className="relative z-10 my-2">
        <p className="text-4xl sm:text-5xl font-black tracking-tight text-emerald-950 tabular-nums">
          {formatINR(displayAmount)}
        </p>
      </div>

      {/* Reassuring Sublabel */}
      {sublabel && (
        <p className="relative z-10 text-xs sm:text-sm font-semibold text-emerald-800">
          ✓ {sublabel}
        </p>
      )}
    </div>
  );
}
