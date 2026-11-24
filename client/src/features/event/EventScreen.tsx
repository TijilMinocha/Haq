import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router';
import { useCase, useUpdateCase } from '@/api/hooks';
import type { CaseView } from '@/api/types';
import type { components } from '@/api/schema';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { StepIndicator } from '@/components/layout/StepIndicator';

type EventType = components['schemas']['EventType'];

interface EventFormProps {
  caseData: CaseView;
  caseId: string;
}

function EventForm({ caseData, caseId }: EventFormProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const updateCase = useUpdateCase(caseId);

  const [subjectName, setSubjectName] = useState(caseData.subject.name ?? '');
  const [eventType, setEventType] = useState<EventType>(
    caseData.event.type ?? 'accidental_death',
  );
  const [eventDate, setEventDate] = useState(
    caseData.event.date ?? new Date().toISOString().slice(0, 10),
  );
  const [nomineeName, setNomineeName] = useState(caseData.nominee.name ?? '');
  const [nomineeRelation, setNomineeRelation] = useState(
    caseData.nominee.relation ?? '',
  );
  const [error, setError] = useState<string | null>(null);

  const isHi = i18n.language !== 'en';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!subjectName.trim()) {
      setError(
        isHi
          ? 'कृपया खाताधारक का नाम भरें'
          : 'Please enter the insured person name',
      );
      return;
    }
    if (!eventDate) {
      setError(
        isHi ? 'कृपया घटना की तारीख चुनें' : 'Please select the date of event',
      );
      return;
    }

    try {
      await updateCase.mutateAsync({
        subject: { name: subjectName.trim() },
        event: { type: eventType, date: eventDate },
        nominee: {
          name: nomineeName.trim() || undefined,
          relation: nomineeRelation.trim() || undefined,
        },
      });
      navigate(`/case/${caseId}/scan`);
    } catch {
      setError(t('errors.unknown_error'));
    }
  };

  return (
    <Card className="p-4 sm:p-6">
      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label={
            isHi
              ? 'खाताधारक का नाम (जिसके नाम बैंक खाता था)'
              : 'Insured Person Name (Account holder)'
          }
          placeholder={isHi ? 'उदा. रमेश कुमार' : 'e.g. Ramesh Kumar'}
          value={subjectName}
          onChange={(e) => setSubjectName(e.target.value)}
          enableVoice
          onVoiceInput={(text) => setSubjectName(text)}
          required
        />

        <div>
          <label className="block text-sm font-semibold text-slate-800 mb-2">
            {isHi ? 'क्या हुआ?' : 'What happened?'}
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {[
              {
                type: 'accidental_death' as EventType,
                hi: 'दुर्घटना में मृत्यु',
                en: 'Accidental death',
                desc: isHi ? 'सड़क, कार्यस्थल, डूबना आदि' : 'Road, workplace, drowning',
                icon: '⚠️',
              },
              {
                type: 'natural_death' as EventType,
                hi: 'सामान्य/बीमारी से मृत्यु',
                en: 'Natural death',
                desc: isHi ? 'बीमारी, हृदय रोग, वृद्धावस्था' : 'Illness, heart, old age',
                icon: '🕊️',
              },
              {
                type: 'accidental_disability' as EventType,
                hi: 'दुर्घटना में विकलांगता',
                en: 'Accidental disability',
                desc: isHi ? 'हाथ, पैर या आँख की क्षति' : 'Loss of limbs, sight',
                icon: '🩹',
              },
            ].map((opt) => (
              <button
                type="button"
                key={opt.type}
                onClick={() => setEventType(opt.type)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                  eventType === opt.type
                    ? 'border-[#0f766e] bg-teal-50 ring-2 ring-[#0f766e]'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="text-xl mb-1">{opt.icon}</div>
                <div className="font-bold text-sm text-slate-900">
                  {isHi ? opt.hi : opt.en}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <Input
          label={isHi ? 'घटना की तारीख' : 'Date of Event'}
          type="date"
          value={eventDate}
          onChange={(e) => setEventDate(e.target.value)}
          required
        />

        <div className="pt-2 border-t border-slate-200 space-y-4">
          <h2 className="text-base font-bold text-slate-900">
            {isHi
              ? 'दावेदार / नॉमिनी (जिसको पैसा मिलेगा)'
              : 'Claimant / Nominee (Beneficiary)'}
          </h2>

          <Input
            label={isHi ? 'नॉमिनी का नाम' : 'Nominee Name'}
            placeholder={isHi ? 'उदा. सुनीता देवी' : 'e.g. Sunita Devi'}
            value={nomineeName}
            onChange={(e) => setNomineeName(e.target.value)}
            enableVoice
            onVoiceInput={(text) => setNomineeName(text)}
          />

          <Input
            label={isHi ? 'खाताधारक से रिश्ता' : 'Relation with Account Holder'}
            placeholder={isHi ? 'उदा. पत्नी, पुत्र, माता' : 'e.g. Wife, Son, Mother'}
            value={nomineeRelation}
            onChange={(e) => setNomineeRelation(e.target.value)}
            enableVoice
            onVoiceInput={(text) => setNomineeRelation(text)}
          />
        </div>

        {error && (
          <div className="rounded-xl bg-red-50 p-3 text-sm font-medium text-red-800 border border-red-200">
            {error}
          </div>
        )}

        <div className="pt-3">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            loading={updateCase.isPending}
          >
            {isHi
              ? 'आगे बढ़ें (पासबुक फ़ोटो लें) →'
              : 'Continue (Scan Passbook) →'}
          </Button>
        </div>
      </form>
    </Card>
  );
}

export function EventScreen() {
  const { i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const caseQuery = useCase(id ?? '');
  const isHi = i18n.language !== 'en';

  return (
    <div className="space-y-6">
      <StepIndicator currentStep="event" />

      <div className="pt-2">
        <h1 className="text-2xl font-bold text-slate-900">
          {isHi ? 'घटना और परिवार की जानकारी' : 'Event and Family Details'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'बीमा खोजने के लिए यह बुनियादी जानकारी भरें। माइक बटन दबाकर बोल भी सकते हैं।'
            : 'Fill in details to find eligible covers. Use the mic icon for voice input.'}
        </p>
      </div>

      {caseQuery.data && id ? (
        <EventForm key={caseQuery.data.id} caseData={caseQuery.data} caseId={id} />
      ) : (
        <div className="py-12 text-center text-slate-500">
          {isHi ? 'लोड हो रहा है...' : 'Loading...'}
        </div>
      )}
    </div>
  );
}
