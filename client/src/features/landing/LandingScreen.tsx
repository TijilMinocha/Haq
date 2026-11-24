import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router';
import { useCreateCase } from '@/api/hooks';
import type { components } from '@/api/schema';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

type ModeChoice = 'claim' | 'protect';
type Language = components['schemas']['Language'];

export function LandingScreen() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const createCase = useCreateCase();

  const [selectedMode, setSelectedMode] = useState<ModeChoice | null>(null);
  const [pin, setPin] = useState('1234');
  const [pinError, setPinError] = useState<string | null>(null);

  const handleStartCase = async (mode: ModeChoice) => {
    setSelectedMode(mode);
  };

  const handleConfirmCreate = async () => {
    if (!/^\d{4}$/.test(pin)) {
      setPinError(i18n.language === 'en' ? 'Please enter a 4-digit numeric PIN' : 'कृपया 4 अंकों का पिन डालें');
      return;
    }
    setPinError(null);

    const lang: Language = i18n.language === 'en' ? 'en' : 'hi';
    const mode = selectedMode ?? 'claim';

    try {
      const result = await createCase.mutateAsync({
        mode,
        language: lang,
        pin,
      });
      navigate(`/case/${result.case_id}/created`, {
        state: { code: result.case_code, pin, mode },
      });
    } catch {
      setPinError(t('errors.unknown_error'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center pt-2 pb-4">
        <span className="inline-block rounded-full bg-teal-100/80 px-3 py-1 text-xs font-semibold text-[#0f766e]">
          {t('landing.badge')}
        </span>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
          {t('landing.title')}
        </h1>
        <p className="mt-3 text-base text-slate-600 max-w-md mx-auto leading-relaxed">
          {t('landing.subtitle')}
        </p>
      </div>

      {selectedMode && (
        <Card highlight className="space-y-4 border-2 border-[#0f766e] bg-teal-50/40 p-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {i18n.language === 'en' ? 'Set 4-digit Case PIN' : '4 अंकों का सुरक्षा पिन चुनें'}
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">
              {i18n.language === 'en'
                ? 'You will need this PIN and your case code to reopen your case later.'
                : 'बाद में केस खोलने के लिए इस पिन और केस कोड की आवश्यकता होगी।'}
            </p>
          </div>

          <div>
            <input
              type="tel"
              maxLength={4}
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
              placeholder="1234"
              className="w-full text-center tracking-widest text-3xl font-bold font-mono h-14 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#0f766e]"
            />
            {pinError && <p className="mt-1 text-sm font-medium text-red-600">{pinError}</p>}
          </div>

          <div className="flex gap-2">
            <Button
              variant="secondary"
              fullWidth
              onClick={() => setSelectedMode(null)}
              disabled={createCase.isPending}
            >
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              fullWidth
              loading={createCase.isPending}
              onClick={handleConfirmCreate}
            >
              {t('common.continue')}
            </Button>
          </div>
        </Card>
      )}

      <div className="space-y-3">
        <button
          type="button"
          onClick={() => handleStartCase('claim')}
          className="w-full text-left rounded-2xl border-2 border-slate-200 bg-white p-5 transition-all hover:border-[#0f766e] hover:shadow-sm active:bg-slate-50 cursor-pointer group"
        >
          <div className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-[#0f766e] text-2xl group-hover:scale-105 transition-transform">
              🏛️
            </span>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                {t('landing.claim_title')}
              </h2>
              <p className="mt-1 text-sm text-slate-600 leading-normal">
                {t('landing.claim_desc')}
              </p>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleStartCase('protect')}
          className="w-full text-left rounded-2xl border border-slate-200 bg-white p-5 transition-all hover:border-[#0f766e] hover:shadow-sm active:bg-slate-50 cursor-pointer group"
        >
          <div className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800 text-2xl group-hover:scale-105 transition-transform">
              🛡️
            </span>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                {t('landing.protect_title')}
              </h2>
              <p className="mt-1 text-sm text-slate-600 leading-normal">
                {t('landing.protect_desc')}
              </p>
            </div>
          </div>
        </button>

        <Link
          to="/resume"
          className="block w-full text-left rounded-2xl border border-slate-200 bg-white p-5 transition-all hover:border-[#0f766e] hover:shadow-sm active:bg-slate-50 group"
        >
          <div className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 text-2xl group-hover:scale-105 transition-transform">
              🔑
            </span>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                {t('landing.resume_title')}
              </h2>
              <p className="mt-1 text-sm text-slate-600 leading-normal">
                {t('landing.resume_desc')}
              </p>
            </div>
          </div>
        </Link>
      </div>

      <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4 text-sm text-slate-500">
        <Link
          to="/operator/login"
          className="hover:text-slate-800 underline underline-offset-4"
        >
          {t('landing.operator_link')}
        </Link>
        <span className="hidden sm:inline">•</span>
        <Link
          to="/demo"
          className="font-semibold text-[#0f766e] hover:underline underline-offset-4"
        >
          {t('landing.demo_link')}
        </Link>
      </div>
    </div>
  );
}
