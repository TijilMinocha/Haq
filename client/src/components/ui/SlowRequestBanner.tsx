import { useEffect, useState } from 'react';
import { useIsFetching, useIsMutating } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { env } from '@/config/env';

export function SlowRequestBanner() {
  const { t } = useTranslation();
  const isFetching = useIsFetching();
  const isMutating = useIsMutating();
  const isBusy = isFetching > 0 || isMutating > 0;
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    if (!isBusy) return;
    const timer = setTimeout(() => setShowBanner(true), env.slowRequestMs);
    return () => {
      clearTimeout(timer);
      setShowBanner(false);
    };
  }, [isBusy]);

  if (!showBanner) return null;

  return (
    <div
      role="status"
      className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-center text-sm font-medium text-amber-900 flex items-center justify-center gap-2"
    >
      <span className="inline-block animate-spin">⏳</span>
      <span>{t('errors.extractor_unavailable')}</span>
    </div>
  );
}
