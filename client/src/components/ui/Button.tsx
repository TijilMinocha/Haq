import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  icon?: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-[#0f766e] text-white hover:bg-[#0d5f58] active:bg-[#0a4742] shadow-xs focus-visible:ring-2 focus-visible:ring-[#0f766e] focus-visible:ring-offset-2',
  secondary:
    'bg-slate-100 text-slate-900 hover:bg-slate-200 active:bg-slate-300 focus-visible:ring-2 focus-visible:ring-slate-400',
  outline:
    'border-2 border-[#0f766e] text-[#0f766e] hover:bg-teal-50 active:bg-teal-100 focus-visible:ring-2 focus-visible:ring-[#0f766e]',
  danger:
    'bg-red-700 text-white hover:bg-red-800 active:bg-red-900 focus-visible:ring-2 focus-visible:ring-red-600',
  ghost:
    'text-slate-700 hover:bg-slate-100 active:bg-slate-200 focus-visible:ring-2 focus-visible:ring-slate-400',
};

const sizeStyles: Record<ButtonSize, string> = {
  // Mobile touch targets must be at least 48px
  sm: 'min-h-[44px] px-3.5 py-2 text-sm',
  md: 'min-h-[48px] px-4 py-2.5 text-base',
  lg: 'min-h-[52px] px-6 py-3 text-lg font-bold',
};

export function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-150 active:scale-[0.98] cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100 select-none ${
        variantStyles[variant]
      } ${sizeStyles[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {loading ? (
        <svg
          className="h-5 w-5 animate-spin text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        icon
      )}
      <span>{children}</span>
    </button>
  );
}
