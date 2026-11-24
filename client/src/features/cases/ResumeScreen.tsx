import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { useResumeCase } from '@/api/hooks';
import { isApiError } from '@/api/errors';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export function ResumeScreen() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const resumeCase = useResumeCase();

  const [code, setCode] = useState('');
  const [pin, setPin] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isHi = i18n.language !== 'en';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const formattedCode = code.trim().toUpperCase();
    if (!/^HAQ-[2-9A-HJKMNP-Z]{4}$/.test(formattedCode)) {
      setErrorMessage(
        isHi
          ? 'केस कोड HAQ-XXXX जैसा होना चाहिए (जैसे HAQ-9A7B)'
          : 'Case code must look like HAQ-XXXX (e.g. HAQ-9A7B)',
      );
      return;
    }

    if (!/^\d{4}$/.test(pin)) {
      setErrorMessage(
        isHi ? 'कृपया 4 अंकों का पिन डालें' : 'Please enter a 4-digit PIN',
      );
      return;
    }

    try {
      const result = await resumeCase.mutateAsync({
        case_code: formattedCode,
        pin,
      });
      // Navigate to the result screen
      navigate(`/case/${result.case_id}/result`);
    } catch (err: unknown) {
      if (isApiError(err, 'too_many_attempts')) {
        const minutes = (err.details as { minutes?: number })?.minutes ?? 15;
        setErrorMessage(t('errors.too_many_attempts', { minutes }));
      } else if (isApiError(err, 'invalid_credentials')) {
        setErrorMessage(t('errors.invalid_credentials'));
      } else if (isApiError(err, 'case_not_found')) {
        setErrorMessage(t('errors.case_not_found'));
      } else {
        setErrorMessage(t('errors.unknown_error'));
      }
    }
  };

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <div className="text-center pt-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
          {isHi ? 'अपना केस खोलें' : 'Resume Your Case'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'अपना 6 अक्षरों का केस कोड और 4 अंकों का सुरक्षा पिन डालें।'
            : 'Enter your case code and 4-digit security PIN.'}
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label={isHi ? 'केस कोड (Case Code)' : 'Case Code'}
            placeholder="HAQ-XXXX"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            helperText={isHi ? 'उदाहरण: HAQ-7K2M' : 'Example: HAQ-7K2M'}
            required
            autoCapitalize="characters"
          />

          <Input
            label={isHi ? '4 अंकों का पिन (PIN)' : '4-digit PIN'}
            type="password"
            maxLength={4}
            placeholder="••••"
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
            required
          />

          {errorMessage && (
            <div className="rounded-xl bg-red-50 p-3 text-sm font-medium text-red-800 border border-red-200">
              {errorMessage}
            </div>
          )}

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={resumeCase.isPending}
            >
              {isHi ? 'केस खोलें →' : 'Open Case →'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
