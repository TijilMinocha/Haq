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
    <div className="space-y-10 sm:space-y-12">
      {/* Hero Banner */}
      <div className="text-center pt-2 sm:pt-4 pb-2 space-y-3 sm:space-y-4 max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-slate-900 leading-tight">
          {t('landing.title')}
        </h1>

        <div className="inline-block bg-emerald-50 border border-emerald-300 rounded-xl px-4 py-1.5 shadow-2xs">
          <p className="text-sm sm:text-base font-extrabold text-emerald-950">
            ✨ {t('landing.hero_highlight')}
          </p>
        </div>

        <p className="text-sm sm:text-base lg:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          {t('landing.subtitle')}
        </p>
      </div>

      {/* Main 2-Column Responsive Section on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Actions / Flow */}
        <div className="lg:col-span-7 space-y-5">
          {selectedMode && (
            <Card highlight className="space-y-4 border-2 border-[#0f766e] bg-teal-50/50 p-5 sm:p-6 shadow-sm">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900">
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

              <div className="flex gap-3">
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
            <div className="flex items-center justify-between px-1">
              <h2 className="text-lg font-bold text-slate-900">
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
              className="w-full text-left rounded-2xl border-2 border-[#0f766e]/40 bg-teal-50/20 p-5 sm:p-6 transition-all hover:border-[#0f766e] hover:shadow-xs active:bg-teal-50/40 cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-[#0f766e] text-2xl sm:text-3xl group-hover:scale-105 transition-transform">
                  🏛️
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-base sm:text-xl font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                      {t('landing.claim_title')}
                    </h3>
                    <span className="text-[#0f766e] text-xl font-bold group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs sm:text-sm text-slate-600 leading-relaxed">
                    {t('landing.claim_desc')}
                  </p>
                </div>
              </div>
            </button>

            {/* Protect Mode Button */}
            <button
              type="button"
              onClick={() => handleStartCase('protect')}
              className="w-full text-left rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 transition-all hover:border-amber-400 hover:shadow-xs active:bg-slate-50 cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800 text-2xl sm:text-3xl group-hover:scale-105 transition-transform">
                  🛡️
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-base sm:text-xl font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                      {t('landing.protect_title')}
                    </h3>
                    <span className="text-slate-400 group-hover:text-[#0f766e] text-xl font-bold group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs sm:text-sm text-slate-600 leading-relaxed">
                    {t('landing.protect_desc')}
                  </p>
                </div>
              </div>
            </button>

            {/* Resume Case Button */}
            <Link
              to="/resume"
              className="block w-full text-left rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 transition-all hover:border-[#0f766e] hover:shadow-xs active:bg-slate-50 group"
            >
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 text-2xl sm:text-3xl group-hover:scale-105 transition-transform">
                  🔑
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-base sm:text-xl font-bold text-slate-900 group-hover:text-[#0f766e] transition-colors">
                      {t('landing.resume_title')}
                    </h3>
                    <span className="text-slate-400 group-hover:text-[#0f766e] text-xl font-bold group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs sm:text-sm text-slate-600 leading-relaxed">
                    {t('landing.resume_desc')}
                  </p>
                </div>
              </div>
            </Link>
          </div>

          {/* Auxiliary Links */}
          <div className="pt-2 flex flex-col sm:flex-row items-center gap-4 text-xs sm:text-sm text-slate-500">
            <Link
              to="/operator/login"
              className="hover:text-slate-900 font-medium underline underline-offset-4"
            >
              🏛️ {t('landing.operator_link')}
            </Link>
            <span className="hidden sm:inline text-slate-300">•</span>
            <Link
              to="/demo"
              className="font-bold text-[#0f766e] hover:underline underline-offset-4"
            >
              🚀 {t('landing.demo_link')}
            </Link>
          </div>
        </div>

        {/* Right Column on Desktop: Scheme Details */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              {t('landing.schemes_title')}
            </h2>
           
          </div>

          <div className="space-y-3.5">
            <Card className="p-4 sm:p-5 border-l-4 border-l-[#0f766e] bg-white space-y-1.5 shadow-2xs hover:shadow-xs transition-shadow">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm sm:text-base text-slate-900">
                  {t('schemes.PMJJBY.name')}
                </h3>
                <span className="font-extrabold text-xs text-[#0f766e] bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-full">
                  ₹2,00,000
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t('schemes.PMJJBY.explanation')}
              </p>
            </Card>

            <Card className="p-4 sm:p-5 border-l-4 border-l-emerald-600 bg-white space-y-1.5 shadow-2xs hover:shadow-xs transition-shadow">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm sm:text-base text-slate-900">
                  {t('schemes.PMSBY.name')}
                </h3>
                <span className="font-extrabold text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                  ₹2,00,000
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t('schemes.PMSBY.explanation')}
              </p>
            </Card>

            <Card className="p-4 sm:p-5 border-l-4 border-l-amber-500 bg-white space-y-1.5 shadow-2xs hover:shadow-xs transition-shadow">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm sm:text-base text-slate-900">
                  {t('schemes.RUPAY_PMJDY.name')}
                </h3>
                <span className="font-extrabold text-xs text-amber-900 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                  ₹2,00,000
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t('schemes.RUPAY_PMJDY.explanation')}
              </p>
            </Card>
          </div>
        </div>
      </div>

      {/* Trust & Privacy Guarantee Section (Full Width Horizontal 3-Column on Desktop) */}
      <div className="pt-6 border-t border-slate-200 space-y-4">
        <div className="text-center max-w-xl mx-auto">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900">
            {t('landing.why_haq_title')}
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-2 shadow-2xs hover:shadow-xs transition-shadow">
            <p className="font-bold text-sm sm:text-base text-slate-900 flex items-center gap-2">
              <span className="text-xl">🪙</span> {t('landing.trust_free')}
            </p>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.trust_free_desc')}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-2 shadow-2xs hover:shadow-xs transition-shadow">
            <p className="font-bold text-sm sm:text-base text-slate-900 flex items-center gap-2">
              <span className="text-xl">🔒</span> {t('landing.trust_privacy')}
            </p>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.trust_privacy_desc')}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-2 shadow-2xs hover:shadow-xs transition-shadow">
            <p className="font-bold text-sm sm:text-base text-slate-900 flex items-center gap-2">
              <span className="text-xl">⚖️</span> {t('landing.trust_rules')}
            </p>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.trust_rules_desc')}
            </p>
          </div>
        </div>
      </div>

      {/* How Haq Works Section (Full Width 3-Column on Desktop) */}
      <div className="pt-6 border-t border-slate-200 space-y-5">
        <div className="text-center max-w-xl mx-auto">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            {t('landing.how_it_works_title')}
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {isHi ? '3 आसान चरणों में आपका अधिकार' : '3 simple steps from passbook to bank'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Card className="p-5 sm:p-6 space-y-2 border-slate-200 bg-white shadow-2xs hover:shadow-xs transition-shadow">
            <div className="flex items-center gap-2 text-3xl mb-1">
              <span>📸</span>
            </div>
            <h3 className="font-bold text-base text-slate-900">
              {t('landing.step1_title')}
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.step1_desc')}
            </p>
          </Card>

          <Card className="p-5 sm:p-6 space-y-2 border-slate-200 bg-white shadow-2xs hover:shadow-xs transition-shadow">
            <div className="flex items-center gap-2 text-3xl mb-1">
              <span>🔍</span>
            </div>
            <h3 className="font-bold text-base text-slate-900">
              {t('landing.step2_title')}
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.step2_desc')}
            </p>
          </Card>

          <Card className="p-5 sm:p-6 space-y-2 border-slate-200 bg-white shadow-2xs hover:shadow-xs transition-shadow">
            <div className="flex items-center gap-2 text-3xl mb-1">
              <span>📄</span>
            </div>
            <h3 className="font-bold text-base text-slate-900">
              {t('landing.step3_title')}
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {t('landing.step3_desc')}
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
