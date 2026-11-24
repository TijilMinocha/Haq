import type { ReactNode } from 'react';
import { Header } from './Header';
import { SlowRequestBanner } from '../ui/SlowRequestBanner';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-teal-100 selection:text-teal-900">
      <SlowRequestBanner />
      <Header />
      <main className="flex-1 pb-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {children}
        </div>
      </main>
      <footer className="border-t border-slate-200 bg-white py-5 px-4 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-6xl flex flex-col sm:flex-row items-center justify-between gap-2">
          <p className="font-semibold text-slate-700">
            हक़ (Haq) — जन सुरक्षा बीमा सहायता पोर्टल
          </p>
          <p className="text-slate-400">
            PMJJBY • PMSBY • RuPay PMJDY Micro-Insurance Claim Assistance
          </p>
        </div>
      </footer>
    </div>
  );
}
