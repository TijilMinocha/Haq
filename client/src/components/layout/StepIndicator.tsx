import { useTranslation } from 'react-i18next';

export type ClaimStep = 'event' | 'scan' | 'result' | 'documents' | 'submit';

interface StepIndicatorProps {
  currentStep: ClaimStep;
}

const steps: { key: ClaimStep; hi: string; en: string }[] = [
  { key: 'event', hi: 'घटना विवरण', en: 'Event Details' },
  { key: 'scan', hi: 'पासबुक स्कैन', en: 'Scan Passbook' },
  { key: 'result', hi: 'बीमा खोज', en: 'Find Covers' },
  { key: 'documents', hi: 'आवश्यक कागज़ात', en: 'Documents' },
  { key: 'submit', hi: 'दावा फ़ॉर्म', en: 'Claim Forms' },
];

const DEFAULT_STEP = { key: 'event' as ClaimStep, hi: 'घटना विवरण', en: 'Event Details' };

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  const { i18n } = useTranslation();
  const currentIndex = steps.findIndex((s) => s.key === currentStep);
  const isHi = i18n.language !== 'en';
  const current = steps[currentIndex] ?? DEFAULT_STEP;

  return (
    <nav
      aria-label="Progress"
      className="-mx-4 -mt-6 mb-6 border-b border-slate-200 bg-white px-4 py-3 shadow-2xs"
    >
      <div className="mx-auto max-w-xl">
        {/* Step Badge and Active Name */}
        <div className="flex items-center justify-between text-xs font-semibold mb-2.5">
          <span className="inline-flex items-center gap-1.5 font-bold text-[#0f766e] bg-teal-50 px-2.5 py-0.5 rounded-full border border-teal-200">
            {isHi
              ? `चरण ${currentIndex + 1} / ${steps.length}`
              : `Step ${currentIndex + 1} of ${steps.length}`}
          </span>
          <span className="font-bold text-slate-900 text-xs sm:text-sm">
            {isHi ? current.hi : current.en}
          </span>
        </div>

        {/* 5-Segmented Mobile-First Progress Bar */}
        <div
          className="grid grid-cols-5 gap-1.5"
          role="progressbar"
          aria-valuenow={currentIndex + 1}
          aria-valuemin={1}
          aria-valuemax={5}
        >
          {steps.map((step, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;
            return (
              <div key={step.key} className="space-y-1">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    isCompleted
                      ? 'bg-[#0f766e]'
                      : isCurrent
                        ? 'bg-[#0f766e] ring-2 ring-teal-200'
                        : 'bg-slate-200'
                  }`}
                />
                <p
                  className={`hidden sm:block text-[11px] text-center font-medium truncate ${
                    isCurrent
                      ? 'font-bold text-[#0f766e]'
                      : isCompleted
                        ? 'text-slate-700'
                        : 'text-slate-400'
                  }`}
                >
                  {isHi ? step.hi : step.en}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
