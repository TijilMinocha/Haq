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
    const entries = Object.entries(doc.fields || {});
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
    <div className="space-y-6">
      <StepIndicator currentStep="documents" />

      <div className="pt-2">
        <h1 className="text-2xl font-bold text-slate-900">
          {isHi ? 'आवश्यक कागज़ात और जाँच' : 'Required Documents & Verification'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
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
        <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800 border border-red-200">
          {uploadError}
        </div>
      )}

      {editingDoc && (
        <Card highlight className="p-4 space-y-3 border-[#0f766e]">
          <h2 className="text-sm font-bold text-slate-900">
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
                {Object.keys(editingDoc.fields || {}).map((f) => (
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

      <div className="space-y-3">
        <h2 className="text-base font-bold text-slate-900">
          {isHi ? 'अपलोड किए गए कागज़ात' : 'Uploaded Documents'} ({documents.length})
        </h2>

        {documents.map((doc) => {
          const isLowConfidence = doc.confidence < 0.6;
          return (
            <Card key={doc.id} className="p-4 space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-bold text-slate-900">
                    {t(`document_kind.${doc.kind}`)}
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                        isLowConfidence
                          ? 'bg-amber-100 text-amber-800'
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

                <div className="flex gap-2">
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

              <div className="bg-slate-50 rounded-lg p-2.5 text-xs text-slate-700 space-y-1">
                {Object.entries(doc.fields || {}).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-500">{k}:</span>
                    <span className="font-medium text-slate-900">
                      {String(v ?? '—')}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          );
        })}
      </div>

      <div className="space-y-3 pt-2">
        <h2 className="text-base font-bold text-slate-900">
          {isHi ? 'दावे के लिए आवश्यक सूची' : 'Document Checklist for Bank'}
        </h2>

        {neededKinds.map((kind) => {
          const isUploaded = documents.some((d) => d.kind === kind);
          return (
            <Card
              key={kind}
              className={`p-4 flex items-center justify-between ${
                isUploaded ? 'bg-emerald-50/30 border-emerald-200' : 'bg-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{isUploaded ? '✅' : '📄'}</span>
                <div>
                  <p className="font-bold text-sm text-slate-900">
                    {t(`document_kind.${kind}`)}
                  </p>
                  <p className="text-xs text-slate-500">
                    {isUploaded
                      ? isHi
                        ? 'अपलोड हो गया'
                        : 'Uploaded'
                      : isHi
                        ? 'आवश्यक कागज़'
                        : 'Required'}
                  </p>
                </div>
              </div>

              {!isUploaded && (
                <div className="flex items-center gap-2">
                  {kind === 'death_certificate' && (
                    <button
                      type="button"
                      disabled={uploadDoc.isPending}
                      onClick={() => handleUploadSample('death_certificate', '/samples/sunita_death_certificate.png', 'sunita_death_certificate.png')}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-[#0f766e] border border-teal-200 hover:bg-teal-100 cursor-pointer disabled:opacity-50"
                    >
                      💡 {isHi ? 'नमूना जोड़ें' : 'Use Sample'}
                    </button>
                  )}
                  {kind === 'rupay_card' && (
                    <button
                      type="button"
                      disabled={uploadDoc.isPending}
                      onClick={() => handleUploadSample('rupay_card', '/samples/sunita_rupay_card.png', 'sunita_rupay_card.png')}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-[#0f766e] border border-teal-200 hover:bg-teal-100 cursor-pointer disabled:opacity-50"
                    >
                      💡 {isHi ? 'नमूना कार्ड' : 'Use Sample'}
                    </button>
                  )}
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
            </Card>
          );
        })}
      </div>

      <div className="pt-3">
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
  );
}
