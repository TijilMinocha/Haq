import { useSyncExternalStore } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation, useNavigate } from 'react-router';
import { setLanguage } from '@/i18n';
import { isOperator, subscribeOperator } from '@/lib/authStore';
import { Logo } from '../ui/Logo';

export function Header() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const operatorLoggedIn = useSyncExternalStore(subscribeOperator, isOperator);

  const isHome = location.pathname === '/';
  const currentLang = i18n.language === 'en' ? 'en' : 'hi';

  const toggleLanguage = () => {
    setLanguage(currentLang === 'hi' ? 'en' : 'hi');
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-xs">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8 py-2.5 sm:py-3.5">
        <div className="flex items-center gap-2 sm:gap-3">
          {!isHome && (
            <button
              type="button"
              onClick={() => navigate(-1)}
              aria-label="Back"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer"
            >
              <svg
                className="h-5 w-5 sm:h-6 sm:w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          )}
          <Link to="/" className="flex items-center gap-2">
            <Logo />
            <div>
              <span className="font-extrabold text-lg sm:text-xl text-slate-900 tracking-tight leading-none block">
                {t('app.name')}
              </span>
              <span className="hidden xs:block text-[11px] font-medium text-slate-500 leading-none mt-0.5">
                {currentLang === 'hi' ? 'बीमा दावा सहायता' : 'Insurance Claim'}
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          {operatorLoggedIn && (
            <Link
              to="/operator"
              className="text-xs font-semibold px-2 py-1 rounded bg-teal-50 text-[#0f766e] border border-teal-200 hover:bg-teal-100 shrink-0"
            >
              {currentLang === 'hi' ? 'बैंक मित्र' : 'Operator'}
            </Link>
          )}

          <button
            type="button"
            onClick={toggleLanguage}
            className="inline-flex min-h-[38px] sm:min-h-[40px] items-center justify-center rounded-lg border border-slate-300 px-2.5 py-1 sm:px-3 sm:py-1.5 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 active:bg-slate-100 cursor-pointer shrink-0"
          >
            {currentLang === 'hi' ? 'English' : 'हिंदी'}
          </button>
        </div>
      </div>
    </header>
  );
}
