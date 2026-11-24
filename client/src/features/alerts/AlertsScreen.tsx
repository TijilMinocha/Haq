import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router';
import { useCase } from '@/api/hooks';
import { Card } from '@/components/ui/Card';

export function AlertsScreen() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const caseQuery = useCase(id ?? '');
  const caseData = caseQuery.data;

  const isHi = i18n.language !== 'en';

  if (!caseData) {
    return (
      <div className="py-12 text-center text-slate-500">
        {t('common.loading')}
      </div>
    );
  }

  const { alerts } = caseData.evaluation;

  return (
    <div className="space-y-6">
      <div className="pt-2 text-center">
        <span className="inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
          🛡️ {isHi ? 'सुरक्षा जाँच (Protect Mode)' : 'Protect Mode Alert'}
        </span>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">
          {isHi ? 'आपके खाते की बीमा स्थिति' : 'Your Insurance Protection Status'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'बीमा चालू रखने और परिवार की सुरक्षा के लिए ये सूचनाएँ ध्यान से देखें।'
            : 'Review notifications to ensure your insurance covers remain active.'}
        </p>
      </div>

      <div className="space-y-3">
        {alerts.length === 0 ? (
          <Card className="p-6 text-center text-slate-600">
            {isHi ? 'कोई सूचना नहीं मिली।' : 'No active alerts for this case.'}
          </Card>
        ) : (
          alerts.map((alert, idx) => {
            const isActive = alert.code === 'alert.cover_active';
            const isLapsed = alert.code === 'alert.cover_lapsed';
            const isExpiring = alert.code === 'alert.rupay_expiring';

            return (
              <Card
                key={idx}
                className={`p-5 space-y-2 border-2 ${
                  isActive
                    ? 'border-emerald-300 bg-emerald-50/40'
                    : isLapsed
                      ? 'border-red-300 bg-red-50/40'
                      : 'border-amber-300 bg-amber-50/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">
                    {isActive ? '✅' : isLapsed ? '⚠️' : isExpiring ? '⏰' : 'ℹ️'}
                  </span>
                  <div className="flex-1">
                    <p
                      className={`font-bold text-base ${
                        isActive
                          ? 'text-emerald-950'
                          : isLapsed
                            ? 'text-red-950'
                            : 'text-amber-950'
                      }`}
                    >
                      {t(alert.code, alert.params as Record<string, unknown>)}
                    </p>

                    {alert.scheme && (
                      <p className="text-xs font-semibold text-slate-600 mt-1">
                        {t(`schemes.${alert.scheme}.name`)}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Helpful advice card */}
      <Card className="p-4 bg-slate-100 border-slate-200 text-xs text-slate-700 space-y-1.5">
        <p className="font-bold text-slate-900">
          💡 {isHi ? 'RuPay कार्ड को चालू रखने का नियम:' : 'How to keep RuPay cover active:'}
        </p>
        <p>
          {isHi
            ? 'दुर्घटना बीमा के लिए हर 90 दिन में कम से कम एक बार RuPay कार्ड का इस्तेमाल ATM, दुकान या बैंक मित्र केंद्र पर अवश्य करें।'
            : 'Perform at least one transaction using your RuPay card every 90 days at an ATM, POS machine or Bank Mitra.'}
        </p>
      </Card>
    </div>
  );
}
