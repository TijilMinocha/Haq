import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router';
import { useLogout, useMe, useOperatorCases } from '@/api/hooks';
import type { CaseSummary } from '@/api/types';
import { formatINR } from '@/lib/format';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export function OperatorCasesScreen() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const logout = useLogout();
  const meQuery = useMe();

  const [search, setSearch] = useState('');
  const casesQuery = useOperatorCases({ q: search || undefined });

  const isHi = i18n.language !== 'en';

  const handleLogout = () => {
    logout();
    navigate('/operator/login');
  };

  const caseList = (casesQuery.data as CaseSummary[] | undefined) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pt-2">
        <div>
          <span className="text-xs font-bold text-[#0f766e] uppercase tracking-wider">
            {isHi ? 'बैंक मित्र पोर्टल' : 'Bank Mitra Portal'}
          </span>
          <h1 className="text-2xl font-bold text-slate-900">
            {meQuery.data?.name || 'Operator'}
          </h1>
          <p className="text-xs text-slate-500">{meQuery.data?.email}</p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate('/')}>
            {isHi ? '+ नया केस' : '+ New Case'}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            {isHi ? 'लॉगआउट' : 'Logout'}
          </Button>
        </div>
      </div>

      <div>
        <input
          type="search"
          placeholder={isHi ? 'केस कोड या नाम से खोजें...' : 'Search by code or name...'}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full min-h-[48px] rounded-xl border border-slate-300 px-4 text-sm bg-white shadow-2xs focus:outline-none focus:ring-2 focus:ring-[#0f766e]"
        />
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-bold text-slate-900">
          {isHi ? 'दर्ज केस सूची' : 'Assigned Cases'} ({caseList.length})
        </h2>

        {casesQuery.isLoading ? (
          <div className="py-8 text-center text-slate-500">
            {t('common.loading')}
          </div>
        ) : caseList.length === 0 ? (
          <Card className="p-8 text-center text-slate-500">
            {isHi ? 'कोई केस नहीं मिला।' : 'No cases found.'}
          </Card>
        ) : (
          caseList.map((c: CaseSummary) => (
            <Link
              key={c.id}
              to={`/case/${c.id}/result`}
              className="block rounded-xl border border-slate-200 bg-white p-4 transition-all hover:border-[#0f766e] hover:shadow-xs active:bg-slate-50"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-mono text-xs font-bold text-[#0f766e] bg-teal-50 px-2 py-0.5 rounded">
                    {c.code}
                  </span>
                  <p className="font-bold text-base text-slate-900 mt-1">
                    {c.subject_name || (isHi ? 'नाम दर्ज नहीं' : 'Unnamed')}
                  </p>
                  <p className="text-xs text-slate-500">
                    {c.mode === 'claim'
                      ? isHi
                        ? 'दावा केस'
                        : 'Claim'
                      : isHi
                        ? 'सुरक्षा जाँच'
                        : 'Protect'}
                  </p>
                </div>

                <div className="text-right">
                  <span className="font-extrabold text-base text-emerald-900 block">
                    {formatINR(c.total_claimable)}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(c.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
