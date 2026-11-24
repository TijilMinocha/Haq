import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { useStartDemo } from '@/api/hooks';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export function DemoScreen() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const startDemo = useStartDemo();

  const [loadingScenarioId, setLoadingScenarioId] = useState<string | null>(null);
  const isHi = i18n.language !== 'en';

  const scenariosList = [
    {
      id: 'sunita_accident',
      title: isHi ? 'सुनीता: सड़क दुर्घटना दावा (₹6,00,000)' : 'Sunita: Accident Claim (₹6,00,000)',
      story: isHi
        ? 'पति रमेश की सड़क दुर्घटना में मृत्यु। PMJJBY, PMSBY और RuPay तीनों मिलकर ₹6 लाख। नाम में वर्तनी अंतर की समस्या।'
        : 'Husband Ramesh died in accident. Eligible for ₹6L across PMJJBY + PMSBY + RuPay. Has name-mismatch blocker.',
      icon: '🚗',
      color: 'border-teal-500 bg-teal-50/40',
    },
    {
      id: 'meena_lien',
      title: isHi ? 'मीना: लीन अवधि (₹0 अपात्र)' : 'Meena: Lien Period (₹0 Ineligible)',
      story: isHi
        ? 'बीमा जुड़ने के 20 दिन बाद सामान्य बीमारी से मृत्यु। 30-दिन लीन अवधि के कारण PMJJBY अपात्र।'
        : 'Husband died of illness 20 days after enrolling. PMJJBY ineligible due to 30-day natural death lien.',
      icon: '⏳',
      color: 'border-slate-300 bg-slate-50/50',
    },
    {
      id: 'raju_protect',
      title: isHi ? 'राजू: सुरक्षा अलर्ट (Protect Mode)' : 'Raju: Cover Check (Protect Mode)',
      story: isHi
        ? 'जीवित खाताधारक अपना बीमा जाँचते हैं। RuPay 12 दिन में समाप्त होने और प्रीमियम बंद होने की चेतावनी।'
        : 'Living user checks active covers. Alerts for lapsed PMJJBY debit and expiring RuPay 90-day window.',
      icon: '🛡️',
      color: 'border-amber-400 bg-amber-50/40',
    },
  ];

  const handleLaunchScenario = async (scenarioId: string) => {
    setLoadingScenarioId(scenarioId);
    try {
      const res = await startDemo.mutateAsync(scenarioId);
      if (scenarioId === 'raju_protect') {
        navigate(`/case/${res.case_id}/alerts`);
      } else {
        navigate(`/case/${res.case_id}/result`);
      }
    } catch {
      // Fallback
    } finally {
      setLoadingScenarioId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="text-center pt-2">
        <span className="inline-block rounded-full bg-teal-100 px-3 py-1 text-xs font-bold text-[#0f766e]">
          DEMO SCENARIOS
        </span>
        <h1 className="mt-2 text-2xl sm:text-3xl font-extrabold text-slate-900">
          {isHi ? 'डेमो परिदृश्य (निर्णायक पैनल)' : 'Live Demo Scenarios'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'एक क्लिक में वास्तविक नियमों और मामलों का परीक्षण करें। पिन: 1234'
            : '1-click test scenarios evaluating deterministic rules. Case PIN: 1234'}
        </p>
      </div>

      <div className="space-y-3">
        {scenariosList.map((sc) => (
          <Card
            key={sc.id}
            className={`p-5 space-y-3 border-2 ${sc.color} transition-all hover:shadow-xs`}
          >
            <div className="flex items-start gap-3">
              <span className="text-3xl">{sc.icon}</span>
              <div className="flex-1">
                <h2 className="text-base font-bold text-slate-900">
                  {sc.title}
                </h2>
                <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                  {sc.story}
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              fullWidth
              loading={loadingScenarioId === sc.id}
              onClick={() => handleLaunchScenario(sc.id)}
            >
              {isHi ? '🚀 यह परिदृश्य चलाएँ' : '🚀 Launch Scenario'}
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
