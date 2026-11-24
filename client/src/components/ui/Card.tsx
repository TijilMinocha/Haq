import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  highlight?: boolean;
}

export function Card({
  children,
  highlight = false,
  className = '',
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-2xl border bg-white p-4 transition-all shadow-xs ${
        highlight
          ? 'border-[#0f766e] ring-1 ring-[#0f766e]/20 bg-teal-50/20'
          : 'border-slate-200'
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
