import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate, useParams } from 'react-router';
import { useCase } from '@/api/hooks';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export function CaseCreatedScreen() {
  const { i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const caseQuery = useCase(id ?? '');
  const caseData = caseQuery.data;

  const caseCode =
    caseData?.code || (location.state as { code?: string })?.code || '';
  const mode =
    caseData?.mode || (location.state as { mode?: string })?.mode || 'claim';

  const isHi = i18n.language !== 'en';

  const handleNext = () => {
    if (mode === 'claim') {
      navigate(`/case/${id}/event`);
    } else {
      navigate(`/case/${id}/scan`);
    }
  };

  return (
    <div className="space-y-6 text-center max-w-md mx-auto">
      <div className="pt-2">
        <span className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 text-3xl">
          ✓
        </span>
        <h1 className="mt-4 text-2xl sm:text-3xl font-extrabold text-slate-900">
          {isHi ? 'केस सफलतापूर्वक दर्ज हुआ' : 'Case Registered Successfully'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'इस कोड को सुरक्षित लिखकर रख लें। बाद में केस खोलने के लिए यह आवश्यक है।'
            : 'Write down this code safely. You will need it to reopen your case.'}
        </p>
      </div>

      <Card highlight className="p-6 border-2 border-[#0f766e] bg-teal-50/50">
        <p className="text-xs font-bold uppercase tracking-wider text-[#0f766e]">
          {isHi ? 'आपका केस कोड' : 'YOUR CASE CODE'}
        </p>
        <div className="my-3 font-mono text-4xl sm:text-5xl font-black tracking-widest text-slate-900 selection:bg-teal-200">
          {caseCode || 'HAQ-....'}
        </div>
        <p className="text-xs font-medium text-slate-500">
          {isHi
            ? '📌 इसे डायरी या कागज़ पर लिख लें'
            : '📌 Write this on a paper or notebook'}
        </p>
      </Card>

      <div className="pt-2">
        <Button variant="primary" size="lg" fullWidth onClick={handleNext}>
          {isHi ? 'आगे बढ़ें (जानकारी भरें) →' : 'Continue (Enter Details) →'}
        </Button>
      </div>
    </div>
  );
}
