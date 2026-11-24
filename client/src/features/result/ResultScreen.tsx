import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router';
import { useCase } from '@/api/hooks';
import type { CoverStatus } from '@/components/ui/StatusBadge';
import { formatDate, formatINR, daysLeftLabel } from '@/lib/format';
import { isSpeechSynthesisSupported, speak, stopSpeaking } from '@/lib/speech';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { HeroAmount } from '@/components/ui/HeroAmount';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { StepIndicator } from '@/components/layout/StepIndicator';

export function ResultScreen() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const caseQuery = useCase(id ?? '');
  const caseData = caseQuery.data;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const isHi = i18n.language !== 'en';

  if (caseQuery.isLoading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-[#0f766e] border-t-transparent" />
        <p className="text-base font-semibold text-slate-700">
          {isHi ? 'बीमा नियमों की जाँच हो रही है...' : 'Evaluating insurance covers...'}
        </p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 font-bold">{t('errors.case_not_found')}</p>
      </div>
    );
  }

  const { evaluation } = caseData;
  const blockers = evaluation.flags.filter((f) => f.severity === 'blocker');
  const otherFlags = evaluation.flags.filter((f) => f.severity !== 'blocker');

  const handleReadAloud = () => {
    if (isSpeaking) {
      stopSpeaking();
      setIsSpeaking(false);
      return;
    }

    const textToSpeak = isHi
      ? `आपके परिवार के लिए कुल ${formatINR(evaluation.total_claimable)} की बीमा राशि का दावा मिल सकता है। इसमें ${evaluation.covers
          .map((c) => `${t(`schemes.${c.scheme}.name`)} से ${formatINR(c.amount)}`)
          .join(', ')} शामिल है।`
      : `Your family is eligible for up to ${formatINR(evaluation.total_claimable)} across covers including ${evaluation.covers
          .map((c) => `${t(`schemes.${c.scheme}.name`)}: ${formatINR(c.amount)}`)
          .join(', ')}.`;

    setIsSpeaking(true);
    speak(textToSpeak, i18n.language);
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <StepIndicator currentStep="result" />

      {/* Main 2-Column Responsive Layout on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Hero Entitlement, Blockers, Deadlines & Primary Action */}
        <div className="lg:col-span-5 space-y-5">
          <HeroAmount
            amount={evaluation.total_claimable}
            label={isHi ? 'कुल दावा योग्य राशि' : 'TOTAL CLAIMABLE AMOUNT'}
            sublabel={
              evaluation.total_claimable > 0
                ? isHi
                  ? 'पासबुक प्रविष्टि व सरकारी जन सुरक्षा नियमों के आधार पर'
                  : 'Based on passbook entries and scheme rules'
                : isHi
                  ? 'कोई सक्रिय दावा नहीं मिला'
                  : 'No active claim found'
            }
          />

          {isSpeechSynthesisSupported() && (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleReadAloud}
                className={`inline-flex items-center gap-2.5 px-6 py-2.5 rounded-full text-xs sm:text-sm font-bold cursor-pointer transition-all shadow-xs ${
                  isSpeaking
                    ? 'bg-emerald-800 text-white shadow-sm ring-2 ring-emerald-400'
                    : 'bg-white text-slate-800 border border-slate-300 hover:bg-slate-50'
                }`}
              >
                {isSpeaking ? (
                  <div className="flex items-center gap-1 h-4">
                    <span className="w-1 bg-white rounded-full wave-bar-1" />
                    <span className="w-1 bg-white rounded-full wave-bar-2" />
                    <span className="w-1 bg-white rounded-full wave-bar-3" />
                    <span className="w-1 bg-white rounded-full wave-bar-4" />
                    <span className="ml-2 font-semibold">
                      {isHi ? 'बोलना बंद करें' : 'Stop Speaking'}
                    </span>
                  </div>
                ) : (
                  <>
                    <span className="text-base">🔊</span>
                    <span>
                      {isHi ? 'परिणाम बोलकर सुनाएँ' : 'Read Out Results'}
                    </span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Blockers Alert if any */}
          {blockers.length > 0 && (
            <div className="rounded-2xl border-2 border-red-300 bg-red-50/95 p-5 space-y-3 shadow-2xs">
              <div className="flex items-center gap-2">
                <span className="text-xl">⛔</span>
                <h2 className="text-sm sm:text-base font-extrabold text-red-950">
                  {isHi
                    ? 'दावा करने से पहले ये सुधार आवश्यक हैं'
                    : 'Required Fixes Before Bank Submission'}
                </h2>
              </div>
              <div className="space-y-2 pt-1">
                {blockers.map((flag, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl bg-white p-3.5 text-xs sm:text-sm font-semibold text-red-900 border border-red-200 shadow-2xs"
                  >
                    <p>
                      {t(`flags.${flag.code}`, flag.params as Record<string, unknown>) ||
                        flag.code}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Deadlines Countdown */}
          {evaluation.deadlines.length > 0 && (
            <Card className="p-5 space-y-3 bg-amber-50/50 border-amber-300 shadow-2xs">
              <div className="flex items-center gap-2">
                <span className="text-xl">⏰</span>
                <h2 className="text-sm sm:text-base font-bold text-slate-900">
                  {isHi ? 'दावा जमा करने की समय सीमा' : 'Claim Submission Deadlines'}
                </h2>
              </div>
              <div className="space-y-2.5">
                {evaluation.deadlines.map((dl, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs sm:text-sm py-1.5 border-b border-amber-200/60 last:border-0"
                  >
                    <div>
                      <span className="font-bold text-slate-800">
                        {t(`schemes.${dl.scheme}.name`)}:
                      </span>{' '}
                      <span className="text-slate-600">
                        {formatDate(dl.due_date, i18n.language)}
                      </span>
                    </div>
                    <span
                      className={`font-bold px-2.5 py-0.5 rounded-full ${
                        dl.days_left <= 7
                          ? 'bg-red-100 text-red-900 border border-red-200'
                          : 'bg-amber-100 text-amber-900 border border-amber-200'
                      }`}
                    >
                      {daysLeftLabel(dl.days_left, t)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Next Step Action Button */}
          <div className="pt-2">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => navigate(`/case/${id}/documents`)}
            >
              {isHi
                ? 'कागज़ात जोड़ें और सुधारें →'
                : 'Provide Documents & Fix Issues →'}
            </Button>
          </div>
        </div>

        {/* Right Column: Scheme Details & Evidence */}
        <div className="lg:col-span-7 space-y-4">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 px-1">
            {isHi ? 'बीमा योजनाओं की स्थिति' : 'Insurance Scheme Status'}
          </h2>

          <div className="space-y-4">
            {evaluation.covers.map((cover) => (
              <Card key={cover.scheme} className="p-5 sm:p-6 space-y-4 bg-white border border-slate-200 shadow-2xs">
                {/* Header: Scheme name and Verification status */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-extrabold text-base sm:text-lg text-slate-900">
                      {t(`schemes.${cover.scheme}.name`)}
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-500 mt-0.5 leading-relaxed">
                      {t(`schemes.${cover.scheme}.explanation`)}
                    </p>
                  </div>
                  <StatusBadge status={cover.status as CoverStatus} />
                </div>

                {/* Amount Row */}
                <div className="flex items-baseline justify-between rounded-xl bg-slate-50 border border-slate-200 px-4 py-3">
                  <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-600">
                    {isHi ? 'दावा राशि' : 'Cover Amount'}
                  </span>
                  <span className="font-mono text-xl sm:text-2xl font-black text-slate-950">
                    {formatINR(cover.amount)}
                  </span>
                </div>

                {/* Evidence & Eligibility Rules */}
                {cover.reasons.length > 0 && (
                  <div className="rounded-xl border border-teal-200/60 bg-teal-50/40 p-3.5 space-y-2 text-xs sm:text-sm text-slate-700">
                    <p className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-[#0f766e]">
                      {isHi ? 'पासबुक प्रविष्टि व नियम' : 'Passbook Evidence & Rule'}
                    </p>
                    {cover.reasons.map((r, rIdx) => (
                      <div key={rIdx} className="flex items-start gap-2 leading-relaxed">
                        <span className="text-[#0f766e] font-bold">✓</span>
                        <span>
                          {t(`reasons.${r.code}`, r.params as Record<string, unknown>) ||
                            r.code}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>

          {/* Non-blocker flags */}
          {otherFlags.length > 0 && (
            <div className="space-y-2.5 pt-2">
              {otherFlags.map((flag, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl p-3.5 text-xs sm:text-sm flex items-start gap-2.5 border ${
                    flag.severity === 'warning'
                      ? 'bg-amber-50 text-amber-900 border-amber-200'
                      : 'bg-sky-50 text-sky-900 border-sky-200'
                  }`}
                >
                  <span className="text-base">{flag.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
                  <span>
                    {t(`flags.${flag.code}`, flag.params as Record<string, unknown>) ||
                      flag.code}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
