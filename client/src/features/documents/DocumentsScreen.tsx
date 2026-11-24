import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router';
import { useCase, useDeleteDocument, useUpdateDocument, useUploadDocument } from '@/api/hooks';
import type { DocumentKind, DocumentView } from '@/api/types';
import { isApiError } from '@/api/errors';
import { compressImage } from '@/lib/image';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { StepIndicator } from '@/components/layout/StepIndicator';

const SAMPLE_MAP: Partial<
  Record<
    DocumentKind,
    { path: string; filename: string; labelHi: string; labelEn: string }
  >
> = {
  death_certificate: {
    path: '/samples/sunita_death_certificate.png',
    filename: 'sunita_death_certificate.png',
    labelHi: 'नमूना मृत्यु प्रमाण पत्र',
    labelEn: 'Use Sample',
  },
  rupay_card: {
    path: '/samples/sunita_rupay_card.png',
    filename: 'sunita_rupay_card.png',
    labelHi: 'नमूना रूपे कार्ड',
    labelEn: 'Use Sample',
  },
  aadhaar_deceased: {
    path: '/samples/sunita_aadhaar.png',
    filename: 'sunita_aadhaar.png',
    labelHi: 'नमूना आधार कार्ड',
    labelEn: 'Use Sample',
  },
  nominee_bank_proof: {
    path: '/samples/sunita_nominee_bank_proof.png',
    filename: 'sunita_nominee_bank_proof.png',
    labelHi: 'नमूना बैंक पासबुक',
    labelEn: 'Use Sample',
  },
  aadhaar_nominee: {
    path: '/samples/sunita_aadhaar_nominee.png',
    filename: 'sunita_aadhaar_nominee.png',
    labelHi: 'नमूना आधार (नॉमिनी)',
    labelEn: 'Use Sample',
  },
};

export function DocumentsScreen() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const caseQuery = useCase(id ?? '');
  const uploadDoc = useUploadDocument(id ?? '');
  const updateDoc = useUpdateDocument(id ?? '');
  const deleteDoc = useDeleteDocument(id ?? '');

  const [activeUploadKind, setActiveUploadKind] = useState<DocumentKind | null>(null);
  const [editingDoc, setEditingDoc] = useState<DocumentView | null>(null);
  const [editFieldName, setEditFieldName] = useState('');
  const [editFieldValue, setEditFieldValue] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const isHi = i18n.language !== 'en';

  if (!caseQuery.data) {
    return (
      <div className="py-12 text-center text-slate-500">
        {t('common.loading')}
      </div>
    );
  }

  const { documents, evaluation } = caseQuery.data;

  const neededKinds: DocumentKind[] = Array.from(
    new Set(
      evaluation.checklist
        .filter((c) => c.required)
        .map((c) => c.document_kind),
    ),
  );

  if (neededKinds.length === 0) {
    neededKinds.push('death_certificate', 'aadhaar_deceased', 'nominee_bank_proof');
  }

  const handleTriggerUpload = (kind: DocumentKind) => {
    setActiveUploadKind(kind);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeUploadKind) return;

    try {
      const compressed = await compressImage(file);
      await uploadDoc.mutateAsync({
        kind: activeUploadKind,
        file: compressed,
      });
      setActiveUploadKind(null);
    } catch (err: unknown) {
      if (isApiError(err, 'document_unreadable')) {
        setUploadError(t('errors.document_unreadable'));
      } else {
        setUploadError(t('errors.unknown_error'));
      }
    }
  };

  const handleUploadSample = async (kind: DocumentKind, samplePath: string, fileName: string) => {
    setUploadError(null);
    try {
      const res = await fetch(samplePath);
      const blob = await res.blob();
      const file = new File([blob], fileName, { type: 'image/png' });
      await uploadDoc.mutateAsync({ kind, file });
    } catch {
      setUploadError(t('errors.unknown_error'));
    }
  };

  const handleStartEdit = (doc: DocumentView) => {
    setEditingDoc(doc);
    const entries = Object.entries(doc.fields || {}).filter(([k]) => k !== 'transactions');
    if (entries[0]) {
      setEditFieldName(entries[0][0]);
      setEditFieldValue(String(entries[0][1] ?? ''));
    }
  };

  const handleSaveEdit = async () => {
    if (!editingDoc || !editFieldName) return;
    try {
      await updateDoc.mutateAsync({
        documentId: editingDoc.id,
        patch: {
          fields: {
            ...editingDoc.fields,
            [editFieldName]: editFieldValue,
          },
        },
      });
      setEditingDoc(null);
    } catch {
      setUploadError(t('errors.unknown_error'));
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <StepIndicator currentStep="documents" />

      <div className="pt-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {isHi ? 'आवश्यक कागज़ात और जाँच' : 'Required Documents & Verification'}
        </h1>
        <p className="mt-1 text-sm sm:text-base text-slate-600">
          {isHi
            ? 'दावा पक्का करने के लिए ये कागज़ात जोड़ें। पढ़े गए विवरण की जाँच कर लें।'
            : 'Upload documents to confirm eligibility and resolve blockers.'}
        </p>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        accept="image/*,application/pdf"
        capture="environment"
        onChange={handleFileSelected}
        className="hidden"
      />

      {uploadError && (
        <div className="rounded-xl bg-red-50 p-3.5 text-sm text-red-800 border border-red-200">
          {uploadError}
        </div>
      )}

      {editingDoc && (
        <Card highlight className="p-4 sm:p-5 space-y-3 border-2 border-[#0f766e] bg-teal-50/40">
          <h2 className="text-sm sm:text-base font-bold text-slate-900">
            {isHi ? 'कागज़ात की जानकारी सुधारें' : 'Correct Extracted Details'} (
            {t(`document_kind.${editingDoc.kind}`)})
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {isHi ? 'फ़ील्ड' : 'Field'}
              </label>
              <select
                value={editFieldName}
                onChange={(e) => {
                  setEditFieldName(e.target.value);
                  const record = editingDoc.fields as Record<string, unknown> | undefined;
                  const val = record?.[e.target.value];
                  setEditFieldValue(String(val ?? ''));
                }}
                className="w-full h-11 rounded-lg border border-slate-300 px-3 text-sm bg-white"
              >
                {Object.keys(editingDoc.fields || {})
                  .filter((f) => f !== 'transactions')
                  .map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {isHi ? 'सही मूल्य' : 'Correct Value'}
              </label>
              <input
                type="text"
                value={editFieldValue}
                onChange={(e) => setEditFieldValue(e.target.value)}
                className="w-full h-11 rounded-lg border border-slate-300 px-3 text-sm bg-white"
              />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setEditingDoc(null)}
            >
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={updateDoc.isPending}
              onClick={handleSaveEdit}
            >
              {t('common.save')}
            </Button>
          </div>
        </Card>
      )}

      {/* 2-Column Responsive Layout on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Checklist & Upload Actions */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              {isHi ? 'दावे के लिए आवश्यक सूची' : 'Document Checklist for Bank'}
            </h2>
            <span className="text-xs text-slate-500 font-medium">
              {documents.length} / {neededKinds.length} {isHi ? 'तैयार' : 'ready'}
            </span>
          </div>

          <div className="space-y-3">
            {neededKinds.map((kind) => {
              const isUploaded = documents.some((d) => d.kind === kind);
              return (
                <Card
                  key={kind}
                  className={`p-4 transition-all ${
                    isUploaded
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : 'bg-white border-slate-200 hover:border-slate-300 shadow-2xs'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl shrink-0">{isUploaded ? '✅' : '📄'}</span>
                      <div>
                        <p className="font-bold text-sm text-slate-900">
                          {t(`document_kind.${kind}`)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {isUploaded
                            ? isHi
                              ? 'अपलोड हो गया'
                              : 'Uploaded & Verified'
                            : isHi
                              ? 'शाखा में जमा करने हेतु आवश्यक'
                              : 'Required by bank for processing'}
                        </p>
                      </div>
                    </div>

                    {!isUploaded && (
                      <div className="flex items-center gap-2 self-end sm:self-auto">
                        {(() => {
                          const sample = SAMPLE_MAP[kind];
                          if (!sample) return null;
                          return (
                            <button
                              type="button"
                              disabled={uploadDoc.isPending}
                              onClick={() => {
                                handleUploadSample(kind, sample.path, sample.filename);
                              }}
                              className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-teal-50 text-[#0f766e] border border-teal-200 hover:bg-teal-100 cursor-pointer disabled:opacity-50"
                            >
                              💡 {isHi ? sample.labelHi : sample.labelEn}
                            </button>
                          );
                        })()}
                        <Button
                          variant="outline"
                          size="sm"
                          loading={uploadDoc.isPending && activeUploadKind === kind}
                          onClick={() => handleTriggerUpload(kind)}
                        >
                          {isHi ? '+ अपलोड करें' : '+ Upload'}
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>

          <div className="pt-2">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => navigate(`/case/${id}/submit`)}
            >
              {isHi ? 'दावा फ़ॉर्म तैयार करें →' : 'Generate Claim Forms →'}
            </Button>
          </div>
        </div>

        {/* Right Column: Uploaded Documents & Guidelines */}
        <div className="lg:col-span-5 space-y-5">
          <div className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-slate-900 px-1">
              {isHi ? 'अपलोड किए गए कागज़ात' : 'Uploaded Documents'} ({documents.length})
            </h2>

            {documents.length === 0 ? (
              <Card className="p-6 text-center text-sm text-slate-500 border-dashed border-2 border-slate-200 bg-slate-50/50">
                <p>📄 {isHi ? 'अभी तक कोई कागज़ अपलोड नहीं किया गया है।' : 'No documents uploaded yet.'}</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => {
                  const isLowConfidence = doc.confidence < 0.6;
                  return (
                    <Card key={doc.id} className="p-4 space-y-3 bg-white border-slate-200 shadow-2xs">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-bold text-sm text-slate-900">
                            {t(`document_kind.${doc.kind}`)}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                                isLowConfidence
                                  ? 'bg-amber-100 text-amber-900'
                                  : 'bg-emerald-100 text-emerald-800'
                              }`}
                            >
                              {isLowConfidence
                                ? isHi
                                  ? '⚠️ जाँच आवश्यक'
                                  : 'Check Details'
                                : isHi
                                  ? '✓ सही पढ़ा गया'
                                  : 'Verified'}
                            </span>
                          </div>
                        </div>

                        <div className="flex gap-1.5">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStartEdit(doc)}
                          >
                            {t('common.edit')}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteDoc.mutate(doc.id)}
                          >
                            🗑️
                          </Button>
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded-lg p-2.5 text-xs text-slate-700 space-y-1.5">
                        {Object.entries(doc.fields || {}).map(([k, v]) => {
                          if (k === 'transactions' && Array.isArray(v)) {
                            return (
                              <div key={k} className="border-t border-slate-200 pt-2 mt-1 space-y-1.5">
                                <div className="flex justify-between items-center text-slate-600 font-medium">
                                  <span>{isHi ? 'पहचाने गए लेन-देन (Transactions):' : 'Detected Transactions:'}</span>
                                  <span className="font-semibold text-slate-700 bg-slate-200/60 px-2 py-0.5 rounded text-[10px]">
                                    {v.length} entries
                                  </span>
                                </div>
                                <div className="space-y-1 pt-0.5 max-h-36 overflow-y-auto">
                                  {(v as Array<{ date?: string; narration?: string; amount?: number; direction?: string }>).map((tx, idx) => (
                                    <div key={idx} className="flex justify-between items-center bg-white border border-slate-200/80 rounded px-2 py-1 text-[11px]">
                                      <div className="truncate max-w-[170px] sm:max-w-[200px]">
                                        <span className="font-mono text-slate-500 mr-1.5">{tx.date}</span>
                                        <span className="font-semibold text-slate-800">{tx.narration}</span>
                                      </div>
                                      <span className={`font-mono font-bold ${tx.direction === 'debit' ? 'text-slate-900' : 'text-emerald-700'}`}>
                                        ₹{Number(tx.amount || 0).toLocaleString('en-IN')}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          }

                          return (
                            <div key={k} className="flex justify-between">
                              <span className="text-slate-500">{k}:</span>
                              <span className="font-medium text-slate-900">
                                {v === null || v === undefined || v === '' ? '—' : String(v)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>

          {/* Bank Proof Assistance & Privacy Note */}
          <div className="rounded-2xl border border-slate-200 bg-teal-50/40 p-4 sm:p-5 space-y-2.5">
            <h3 className="font-bold text-sm text-teal-950 flex items-center gap-1.5">
              <span>🔒</span>
              {isHi ? 'दस्तावेज़ सुरक्षा एवं बैंक नियम' : 'Document Privacy & Bank Rules'}
            </h3>
            <ul className="text-xs text-slate-600 space-y-1.5 leading-relaxed">
              <li>
                • <strong>{isHi ? 'आधार नंबर सुरक्षित:' : 'Masked Aadhaar:'}</strong>{' '}
                {isHi
                  ? 'केवल अंतिम 4 अंक पढ़े जाते हैं। पूरा आधार कभी रिकॉर्ड नहीं किया जाता।'
                  : 'Only last 4 digits are read. Full Aadhaar is never saved.'}
              </li>
              <li>
                • <strong>{isHi ? 'स्व-प्रमाणित प्रतियाँ:' : 'Self-Attested Copies:'}</strong>{' '}
                {isHi
                  ? 'शाखा में सभी फोटोकॉपी पर नॉमिनी के हस्ताक्षर (Sign) होने चाहिए।'
                  : 'All photocopy submissions must be signed by the nominee.'}
              </li>
              <li>
                • <strong>{isHi ? 'ओरिजिनल कागज़ न सौंपें:' : 'Retain Originals:'}</strong>{' '}
                {isHi
                  ? 'मूल मृत्यु प्रमाण पत्र अपने पास रखें, बैंक को केवल सत्यापित कॉपी दें।'
                  : 'Show original death certificate for verification, surrender only copies.'}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
