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
        <div className="mx-auto max-w-xl px-4 py-6">{children}</div>
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 px-4 text-center text-xs text-slate-500">
        <p>हक़ (Haq) — जन सुरक्षा बीमा सहायता</p>
      </footer>
    </div>
  );
}
