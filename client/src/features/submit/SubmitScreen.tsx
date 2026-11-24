import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router';
import { useCase } from '@/api/hooks';
import { downloadEscalation, downloadForm } from '@/api/downloads';
import { isApiError } from '@/api/errors';
import type { Scheme } from '@/api/types';
import { daysLeftLabel, formatDate } from '@/lib/format';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { StepIndicator } from '@/components/layout/StepIndicator';

export function SubmitScreen() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const caseQuery = useCase(id ?? '');
  const caseData = caseQuery.data;

  const [downloadingScheme, setDownloadingScheme] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const isHi = i18n.language !== 'en';

  if (!caseData) {
    return (
      <div className="py-12 text-center text-slate-500">
        {t('common.loading')}
      </div>
    );
  }

  const { evaluation } = caseData;
  const eligibleCovers = evaluation.covers.filter(
    (c) => c.status === 'eligible' || c.status === 'likely_eligible',
  );

  const handleDownload = async (scheme: Scheme) => {
    if (!id) return;
    setDownloadingScheme(scheme);
    setDownloadError(null);
    try {
      await downloadForm(id, scheme);
    } catch (err: unknown) {
      if (isApiError(err, 'form_not_applicable')) {
        setDownloadError(t('errors.form_not_applicable'));
      } else {
        setDownloadError(t('errors.unknown_error'));
      }
    } finally {
      setDownloadingScheme(null);
    }
  };

  const handleDownloadEscalation = async (scheme: Scheme) => {
    if (!id) return;
    setDownloadingScheme(`escalation-${scheme}`);
    setDownloadError(null);
    try {
      await downloadEscalation(id, scheme);
    } catch {
      setDownloadError(t('errors.unknown_error'));
    } finally {
      setDownloadingScheme(null);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <StepIndicator currentStep="submit" />

      <div className="pt-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {isHi ? 'दावा फ़ॉर्म और बैंक में जमा करना' : 'Claim Forms & Bank Submission'}
        </h1>
        <p className="mt-1 text-sm sm:text-base text-slate-600">
          {isHi
            ? 'भरा हुआ फ़ॉर्म डाउनलोड करें, प्रिंट करें और कागज़ात के साथ बैंक शाखा में जमा करें।'
            : 'Download pre-filled bilingual forms, print them, and submit to the bank branch.'}
        </p>
      </div>

      {downloadError && (
        <div className="rounded-xl bg-red-50 p-3.5 text-sm text-red-800 border border-red-200">
          {downloadError}
        </div>
      )}

      {/* 2-Column Responsive Layout on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Pre-filled Forms & Deadlines */}
        <div className="lg:col-span-7 space-y-5">
          <div className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-slate-900 px-1">
              {isHi ? 'दावा आवेदन पत्र (PDF)' : 'Pre-filled Claim Forms (PDF)'}
            </h2>

            {eligibleCovers.map((cover) => (
              <Card key={cover.scheme} className="p-4 sm:p-5 space-y-3.5 bg-white border-slate-200 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">
                      {t(`schemes.${cover.scheme}.name`)}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {isHi ? 'द्विभाषी (हिंदी + अंग्रेज़ी) आवेदन पत्र' : 'Bilingual claim application form'}
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    size="md"
                    loading={downloadingScheme === cover.scheme}
                    onClick={() => handleDownload(cover.scheme as Scheme)}
                  >
                    📥 {t('common.download')}
                  </Button>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-t border-slate-100 pt-3 gap-2 text-xs">
                  <span className="text-slate-600">
                    {isHi ? 'बैंक से देरी या आनाकानी होने पर:' : 'Escalation letter if bank delays:'}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    loading={downloadingScheme === `escalation-${cover.scheme}`}
                    onClick={() => handleDownloadEscalation(cover.scheme as Scheme)}
                  >
                    📜 {isHi ? 'शिकायत पत्र डाउनलोड करें' : 'Escalation Letter'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {evaluation.deadlines.length > 0 && (
            <Card className="p-4 sm:p-5 bg-amber-50/60 border-amber-200 space-y-2.5">
              <h2 className="text-sm sm:text-base font-bold text-amber-950 flex items-center gap-1.5">
                <span>⏰</span>
                <span>{isHi ? 'अंतिम तिथि का ध्यान रखें' : 'Important Deadlines'}</span>
              </h2>
              <div className="space-y-2 text-xs">
                {evaluation.deadlines.map((dl, idx) => (
                  <div key={idx} className="flex justify-between items-center py-1 border-b border-amber-200/50 last:border-0">
                    <span className="text-slate-800 font-medium">
                      {t(`schemes.${dl.scheme}.name`)} ({formatDate(dl.due_date, i18n.language)})
                    </span>
                    <span className="font-bold text-amber-900 bg-amber-200/70 px-2.5 py-0.5 rounded-full">
                      {daysLeftLabel(dl.days_left, t)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: 4 Steps at Bank Branch & Counter Defense */}
        <div className="lg:col-span-5 space-y-5">
          <Card className="p-5 sm:p-6 space-y-4 bg-white border-slate-200 shadow-2xs">
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              🏛️ {isHi ? 'बैंक शाखा में जमा करने के 4 नियम' : '4 Steps at Bank Branch'}
            </h2>
            <ol className="list-decimal pl-5 space-y-2.5 text-xs sm:text-sm text-slate-700 leading-relaxed">
              <li>
                <strong className="text-slate-900">
                  {isHi ? 'फ़ॉर्म का प्रिंट लें:' : 'Print the form:'}
                </strong>{' '}
                {isHi
                  ? 'ऊपर दिए गए बटन से फ़ॉर्म डाउनलोड कर प्रिंट करवा लें।'
                  : 'Download and print the bilingual claim details form.'}
              </li>
              <li>
                <strong className="text-slate-900">
                  {isHi ? 'कागज़ात साथ जोड़ें:' : 'Attach proofs:'}
                </strong>{' '}
                {isHi
                  ? 'मृत्यु प्रमाण पत्र, आधार, और नॉमिनी के बैंक खाते का कैंसिल चेक/पासबुक की कॉपी लगाएँ।'
                  : 'Attach death certificate, Aadhaar, and claimant bank proof.'}
              </li>
              <li>
                <strong className="text-slate-900">
                  {isHi ? 'संबंधित बैंक शाखा जाएँ:' : 'Visit the home branch:'}
                </strong>{' '}
                {isHi
                  ? 'जिस शाखा में खाता था, वहाँ के शाखा प्रबंधक (Branch Manager) या बैंक मित्र को दें।'
                  : 'Submit to the branch manager or Bank Mitra where account is held.'}
              </li>
              <li>
                <strong className="text-slate-900">
                  {isHi ? 'पावती (Receipt) अवश्य लें:' : 'Always obtain receipt:'}
                </strong>{' '}
                {isHi
                  ? 'फ़ॉर्म जमा करने के बाद बैंक की सील और तारीख वाली पावती (acknowledgment) ज़रूर लें।'
                  : 'Get a stamped and dated receipt with claim reference number.'}
              </li>
            </ol>
          </Card>

          <div className="rounded-2xl border border-slate-200 bg-slate-100/70 p-4 sm:p-5 space-y-2">
            <h3 className="font-bold text-xs sm:text-sm text-slate-900 flex items-center gap-1.5">
              <span>💡</span>
              {isHi ? 'यदि बैंक अधिकारी मना करे तो?' : 'If Bank Branch Declines?'}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {isHi
                ? 'शाखा को बताएँ कि पासबुक में कटी प्रीमियम एंट्री ही पॉलिसी का पुख्ता प्रमाण है। यदि वे अस्वीकार करें तो ऊपर दिया गया शिकायत पत्र (Escalation) शाखा प्रबंधक को सौंपें।'
                : 'Remind the officer that the premium auto-debit entry in the passbook is legal proof of cover. If they refuse, hand over the generated escalation letter.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
