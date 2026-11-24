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

  const isHi = i18n.language !== 'en';

  const handleStartCase = (mode: ModeChoice) => {
    setSelectedMode(mode);
    // Smooth scroll to PIN input
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleConfirmCreate = async () => {
    if (!/^\d{4}$/.test(pin)) {
      setPinError(isHi ? 'कृपया 4 अंकों का पिन डालें' : 'Please enter a 4-digit numeric PIN');
      return;
    }
    setPinError(null);

    const lang: Language = isHi ? 'hi' : 'en';
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
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center pt-2 pb-2 space-y-3">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl leading-tight">
          {t('landing.title')}
        </h1>

        <div className="inline-block bg-emerald-50 border border-emerald-300 rounded-xl px-4 py-1.5 shadow-2xs">
          <p className="text-sm sm:text-base font-extrabold text-emerald-950">
            ✨ {t('landing.hero_highlight')}
          </p>
        </div>

        <p className="text-sm sm:text-base text-slate-600 max-w-lg mx-auto leading-relaxed pt-1">
          {t('landing.subtitle')}
        </p>
      </div>

      {/* PIN Confirmation Modal / Card */}
      {selectedMode && (
        <Card highlight className="space-y-4 border-2 border-[#0f766e] bg-teal-50/50 p-5 shadow-sm">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {isHi ? '4 अंकों का सुरक्षा पिन चुनें' : 'Set 4-digit Case PIN'}
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
              {isHi
                ? 'बाद में केस खोलने के लिए इस पिन और केस कोड की आवश्यकता होगी।'
                : 'You will need this PIN and your case code to reopen your case later.'}
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
            {pinError && <p className="mt-1.5 text-sm font-medium text-red-600">{pinError}</p>}
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

      {/* Main Options / CTA Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-base font-bold text-slate-900">
            {t('landing.actions_title')}
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            {isHi ? 'कोई भी विकल्प चुनें' : 'Select an option'}
          </span>
        </div>

        {/* Claim Mode Button */}
        <button
          type="button"
          onClick={() => handleStartCase('claim')}
          className="w-full text-left rounded-2xl border-2 border-[#0f766e]/40 bg-teal-50/20 p-4 sm:p-5 transition-all hover:border-[#0f766e] hover:shadow-xs active:bg-teal-50/40 cursor-pointer group"
        >
          <div className="flex items-start gap-3.5">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-[#0f766e] text-2xl group-hover:scale-105 transition-transform">
              🏛️
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                  {t('landing.claim_title')}
                </h3>
                <span className="text-[#0f766e] text-lg font-bold">→</span>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-slate-600 leading-normal">
                {t('landing.claim_desc')}
              </p>
            </div>
          </div>
        </button>

        {/* Protect Mode Button */}
        <button
          type="button"
          onClick={() => handleStartCase('protect')}
          className="w-full text-left rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 transition-all hover:border-amber-400 hover:shadow-xs active:bg-slate-50 cursor-pointer group"
        >
          <div className="flex items-start gap-3.5">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800 text-2xl group-hover:scale-105 transition-transform">
              🛡️
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                  {t('landing.protect_title')}
                </h3>
                <span className="text-slate-400 group-hover:text-[#0f766e] text-lg font-bold">→</span>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-slate-600 leading-normal">
                {t('landing.protect_desc')}
              </p>
            </div>
          </div>
        </button>

        {/* Resume Case Button */}
        <Link
          to="/resume"
          className="block w-full text-left rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 transition-all hover:border-[#0f766e] hover:shadow-xs active:bg-slate-50 group"
        >
          <div className="flex items-start gap-3.5">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 text-2xl group-hover:scale-105 transition-transform">
              🔑
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                  {t('landing.resume_title')}
                </h3>
                <span className="text-slate-400 group-hover:text-[#0f766e] text-lg font-bold">→</span>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-slate-600 leading-normal">
                {t('landing.resume_desc')}
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* How Haq Works Section */}
      <div className="pt-2 space-y-3">
        <h2 className="text-lg font-bold text-slate-900 px-1">
          {t('landing.how_it_works_title')}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Card className="p-4 space-y-1.5 border-slate-200 bg-white">
            <span className="text-2xl">📸</span>
            <h3 className="font-bold text-sm text-slate-900">
              {t('landing.step1_title')}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {t('landing.step1_desc')}
            </p>
          </Card>

          <Card className="p-4 space-y-1.5 border-slate-200 bg-white">
            <span className="text-2xl">🔍</span>
            <h3 className="font-bold text-sm text-slate-900">
              {t('landing.step2_title')}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {t('landing.step2_desc')}
            </p>
          </Card>

          <Card className="p-4 space-y-1.5 border-slate-200 bg-white">
            <span className="text-2xl">📄</span>
            <h3 className="font-bold text-sm text-slate-900">
              {t('landing.step3_title')}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {t('landing.step3_desc')}
            </p>
          </Card>
        </div>
      </div>

      {/* 3 Schemes Explainer Section */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-slate-900 px-1">
          {t('landing.schemes_title')}
        </h2>

        <div className="space-y-2.5">
          <Card className="p-4 border-l-4 border-l-[#0f766e] bg-white space-y-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900">
                {t('schemes.PMJJBY.name')}
              </h3>
              <span className="font-bold text-xs text-[#0f766e] bg-teal-50 px-2 py-0.5 rounded">
                ₹2,00,000
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {t('schemes.PMJJBY.explanation')}
            </p>
          </Card>

          <Card className="p-4 border-l-4 border-l-emerald-600 bg-white space-y-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900">
                {t('schemes.PMSBY.name')}
              </h3>
              <span className="font-bold text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                ₹2,00,000
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {t('schemes.PMSBY.explanation')}
            </p>
          </Card>

          <Card className="p-4 border-l-4 border-l-amber-500 bg-white space-y-1">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900">
                {t('schemes.RUPAY_PMJDY.name')}
              </h3>
              <span className="font-bold text-xs text-amber-900 bg-amber-50 px-2 py-0.5 rounded">
                ₹2,00,000
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {t('schemes.RUPAY_PMJDY.explanation')}
            </p>
          </Card>
        </div>
      </div>

      {/* Trust & Privacy Guarantee Section */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-slate-900 px-1">
          {t('landing.why_haq_title')}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-1">
            <p className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
              <span>🪙</span> {t('landing.trust_free')}
            </p>
            <p className="text-[11px] text-slate-600 leading-normal">
              {t('landing.trust_free_desc')}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-1">
            <p className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
              <span>🔒</span> {t('landing.trust_privacy')}
            </p>
            <p className="text-[11px] text-slate-600 leading-normal">
              {t('landing.trust_privacy_desc')}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-1">
            <p className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
              <span>⚖️</span> {t('landing.trust_rules')}
            </p>
            <p className="text-[11px] text-slate-600 leading-normal">
              {t('landing.trust_rules_desc')}
            </p>
          </div>
        </div>
      </div>

      {/* Footer Auxiliary Links */}
      <div className="pt-2 pb-4 flex flex-col sm:flex-row items-center justify-center gap-4 text-xs text-slate-500">
        <Link
          to="/operator/login"
          className="hover:text-slate-800 underline underline-offset-4"
        >
          {t('landing.operator_link')}
        </Link>
        <span className="hidden sm:inline">•</span>
        <Link
          to="/demo"
          className="font-bold text-[#0f766e] hover:underline underline-offset-4"
        >
          {t('landing.demo_link')}
        </Link>
      </div>
    </div>
  );
}
