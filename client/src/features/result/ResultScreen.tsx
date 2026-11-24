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
      <div className="py-16 text-center space-y-3">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#0f766e] border-t-transparent" />
        <p className="text-sm font-medium text-slate-600">
          {isHi ? 'बीमा नियमों की जाँच हो रही है...' : 'Evaluating insurance covers...'}
        </p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{t('errors.case_not_found')}</p>
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
    <div className="space-y-6">
      <StepIndicator currentStep="result" />

      {/* Hero Entitlement Ledger and Tactile Read-Aloud */}
      <div className="space-y-3">
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
              className={`inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full text-xs font-bold cursor-pointer transition-all shadow-xs ${
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
                  <span className="ml-1.5">
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
      </div>

      {/* Blockers Alert if any */}
      {blockers.length > 0 && (
        <div className="rounded-2xl border-2 border-red-300 bg-red-50/90 p-4 space-y-2.5 shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="text-xl">⛔</span>
            <h2 className="text-sm font-bold text-red-950">
              {isHi
                ? 'दावा करने से पहले ये 2 सुधार आवश्यक हैं'
                : 'Required Fixes Before Bank Submission'}
            </h2>
          </div>
          <div className="space-y-2 pt-1">
            {blockers.map((flag, idx) => (
              <div
                key={idx}
                className="rounded-xl bg-white p-3 text-xs font-semibold text-red-900 border border-red-200 shadow-2xs"
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

      {/* Passbook Ledger Scheme Cards */}
      <div className="space-y-3">
        <h2 className="text-base font-bold text-slate-900 px-1">
          {isHi ? 'बीमा योजनाओं की स्थिति' : 'Insurance Scheme Status'}
        </h2>

        {evaluation.covers.map((cover) => (
          <Card key={cover.scheme} className="p-4 sm:p-5 space-y-3.5 bg-white border border-slate-200">
            {/* Header: Scheme name and Verification status */}
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-extrabold text-base text-slate-900">
                  {t(`schemes.${cover.scheme}.name`)}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                  {t(`schemes.${cover.scheme}.explanation`)}
                </p>
              </div>
              <StatusBadge status={cover.status as CoverStatus} />
            </div>

            {/* Passbook Ledger Amount Row */}
            <div className="flex items-baseline justify-between rounded-xl bg-slate-50 border border-slate-200 px-3.5 py-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                {isHi ? 'दावा राशि' : 'Cover Amount'}
              </span>
              <span className="font-mono text-xl font-black text-slate-950">
                {formatINR(cover.amount)}
              </span>
            </div>

            {/* Evidence & Eligibility Rules */}
            {cover.reasons.length > 0 && (
              <div className="rounded-xl border border-teal-200/60 bg-teal-50/30 p-3 space-y-1.5 text-xs text-slate-700">
                <p className="text-[10px] font-bold uppercase tracking-wider text-[#0f766e]">
                  {isHi ? 'पासबुक प्रविष्टि व नियम' : 'Passbook Evidence & Rule'}
                </p>
                {cover.reasons.map((r, rIdx) => (
                  <div key={rIdx} className="flex items-start gap-1.5 leading-normal">
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

      {/* Deadlines Countdown */}
      {evaluation.deadlines.length > 0 && (
        <Card className="p-4 space-y-3 bg-amber-50/40 border-amber-300 shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="text-lg">⏰</span>
            <h2 className="text-sm font-bold text-slate-900">
              {isHi ? 'दावा जमा करने की समय सीमा' : 'Claim Submission Deadlines'}
            </h2>
          </div>
          <div className="space-y-2">
            {evaluation.deadlines.map((dl, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-xs py-1.5 border-b border-amber-200/50 last:border-0"
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

      {/* Non-blocker flags */}
      {otherFlags.length > 0 && (
        <div className="space-y-2">
          {otherFlags.map((flag, idx) => (
            <div
              key={idx}
              className={`rounded-xl p-3 text-xs flex items-start gap-2 border ${
                flag.severity === 'warning'
                  ? 'bg-amber-50 text-amber-900 border-amber-200'
                  : 'bg-sky-50 text-sky-900 border-sky-200'
              }`}
            >
              <span>{flag.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
              <span>
                {t(`flags.${flag.code}`, flag.params as Record<string, unknown>) ||
                  flag.code}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Next Step Action */}
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
  );
}
