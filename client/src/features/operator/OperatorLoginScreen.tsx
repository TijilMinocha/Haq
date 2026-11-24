import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { useLogin } from '@/api/hooks';
import { isApiError } from '@/api/errors';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export function OperatorLoginScreen() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const loginMutation = useLogin();

  const [email, setEmail] = useState('mitra@haq.demo');
  const [password, setPassword] = useState('haq-demo-2026');
  const [error, setError] = useState<string | null>(null);

  const isHi = i18n.language !== 'en';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await loginMutation.mutateAsync({ email, password });
      navigate('/operator');
    } catch (err: unknown) {
      if (isApiError(err, 'invalid_credentials')) {
        setError(t('errors.invalid_credentials'));
      } else {
        setError(t('errors.unknown_error'));
      }
    }
  };

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <div className="text-center pt-2">
        <span className="flex h-14 w-14 mx-auto items-center justify-center rounded-2xl bg-teal-100 text-[#0f766e] text-2xl">
          🏦
        </span>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">
          {isHi ? 'बैंक मित्र / ऑपरेटर लॉगिन' : 'Bank Mitra / Operator Login'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'ग्रामीण बैंक मित्र और ग्राहक सेवा केंद्र (CSP) के लिए।'
            : 'For authorized Bank Mitras and CSP operators.'}
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label={isHi ? 'ईमेल (Email)' : 'Email'}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            label={isHi ? 'पासवर्ड (Password)' : 'Password'}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && (
            <div className="rounded-xl bg-red-50 p-3 text-sm font-medium text-red-800 border border-red-200">
              {error}
            </div>
          )}

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loginMutation.isPending}
            >
              {isHi ? 'लॉगिन करें →' : 'Sign In →'}
            </Button>
          </div>
        </form>
      </Card>

      <div className="rounded-xl bg-slate-100 p-3 text-xs text-slate-600 text-center space-y-1">
        <p className="font-semibold text-slate-800">
          {isHi ? 'डेमो खाता:' : 'Demo Credentials:'}
        </p>
        <p>mitra@haq.demo / haq-demo-2026</p>
      </div>
    </div>
  );
}
