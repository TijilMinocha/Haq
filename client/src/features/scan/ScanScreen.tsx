import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router';
import { useCase, useUploadDocument } from '@/api/hooks';
import { isApiError } from '@/api/errors';
import { compressImage } from '@/lib/image';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { StepIndicator } from '@/components/layout/StepIndicator';

export function ScanScreen() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const caseQuery = useCase(id ?? '');
  const uploadDoc = useUploadDocument(id ?? '');

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showTips, setShowTips] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const isHi = i18n.language !== 'en';
  const mode = caseQuery.data?.mode ?? 'claim';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setErrorMessage(null);
    setShowTips(false);

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const compressed = await compressImage(selectedFile);
      const updatedCase = await uploadDoc.mutateAsync({
        kind: 'passbook',
        file: compressed,
      });

      if (updatedCase.mode === 'protect') {
        navigate(`/case/${id}/alerts`);
      } else {
        navigate(`/case/${id}/result`);
      }
    } catch (err: unknown) {
      if (isApiError(err, 'document_unreadable')) {
        setShowTips(true);
        setErrorMessage(t('errors.document_unreadable'));
      } else if (isApiError(err, 'extractor_unavailable')) {
        setErrorMessage(t('errors.extractor_unavailable'));
      } else if (isApiError(err, 'file_too_large')) {
        setErrorMessage(t('errors.file_too_large'));
      } else if (isApiError(err, 'unsupported_file')) {
        setErrorMessage(t('errors.unsupported_file'));
      } else {
        setErrorMessage(t('errors.unknown_error'));
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRetake = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setErrorMessage(null);
    setShowTips(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      {mode === 'claim' && <StepIndicator currentStep="scan" />}

      <div className="pt-2">
        <h1 className="text-2xl font-bold text-slate-900">
          {isHi ? 'बैंक पासबुक की फ़ोटो लें' : 'Photograph Bank Passbook'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {isHi
            ? 'पासबुक का वह पन्ना जिसमें बैंक खाता नंबर और प्रीमियम कटने की एंट्री दिखती हो।'
            : 'Capture the page showing account number and insurance premium debits.'}
        </p>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        accept="image/*,application/pdf"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Hidden file input / upload prompt */}
      {!selectedFile && (
        <Card className="p-8 text-center border-2 border-dashed border-slate-300 hover:border-[#0f766e] bg-white transition-colors">
          <div className="flex flex-col items-center justify-center space-y-4">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-50 text-[#0f766e] text-3xl">
              📸
            </span>
            <div>
              <p className="text-base font-bold text-slate-800">
                {isHi ? 'कैमरा चालू करें या फ़ोटो चुनें' : 'Take photo or choose file'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {isHi
                  ? 'साफ़ रोशनी में पासबुक को सीधा रखकर फ़ोटो लें'
                  : 'Ensure good lighting and legible numbers'}
              </p>
            </div>
            <Button
              variant="primary"
              size="lg"
              onClick={() => fileInputRef.current?.click()}
            >
              {isHi ? '📷 फ़ोटो खींचें / अपलोड करें' : '📷 Take Photo / Upload'}
            </Button>
          </div>
        </Card>
      )}

      {/* Preview and Confirm */}
      {selectedFile && (
        <Card className="p-5 space-y-4">
          <div className="relative rounded-xl overflow-hidden bg-slate-900 aspect-4/3 flex items-center justify-center">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Passbook preview"
                className="max-h-full max-w-full object-contain"
              />
            ) : (
              <div className="text-white text-sm font-medium p-4 text-center">
                📄 {selectedFile.name}
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <Button
              variant="secondary"
              fullWidth
              disabled={isProcessing}
              onClick={handleRetake}
            >
              {isHi ? '🔄 दोबारा लें' : '🔄 Retake'}
            </Button>
            <Button
              variant="primary"
              fullWidth
              loading={isProcessing}
              onClick={handleUpload}
            >
              {isProcessing
                ? isHi
                  ? 'जाँच रहे हैं...'
                  : 'Reading OCR...'
                : isHi
                  ? 'बीमा खोजें →'
                  : 'Find Covers →'}
            </Button>
          </div>

          {isProcessing && (
            <p className="text-xs text-center text-slate-500 animate-pulse">
              {isHi
                ? 'पासबुक से प्रविष्टियाँ पढ़ी जा रही हैं (2-5 सेकंड लग सकते हैं)...'
                : 'Extracting bank entries from passbook (2-5 seconds)...'}
            </p>
          )}
        </Card>
      )}

      {/* Error and Retake Tips */}
      {errorMessage && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-900 border border-red-200 space-y-2">
          <p className="font-bold flex items-center gap-1.5">
            <span>⚠️</span> {errorMessage}
          </p>
          {showTips && (
            <div className="text-xs text-red-800 space-y-1 pt-1 border-t border-red-200">
              <p className="font-semibold">
                {isHi ? 'अच्छी फ़ोटो के लिए सुझाव:' : 'Tips for a clearer photo:'}
              </p>
              <ul className="list-disc pl-4 space-y-0.5">
                <li>
                  {isHi
                    ? 'पासबुक को किसी समतल सतह पर रखें'
                    : 'Place passbook flat on a table'}
                </li>
                <li>
                  {isHi
                    ? 'पर्याप्त रोशनी हो और परछाई न पड़े'
                    : 'Use adequate lighting without glare'}
                </li>
                <li>
                  {isHi
                    ? 'कैमरा हिलाए बिना साफ़ फ़ोटो लें'
                    : 'Hold phone steady to avoid motion blur'}
                </li>
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Helpful guidance */}
      <div className="rounded-xl bg-slate-100 p-4 text-xs text-slate-600 space-y-1.5">
        <p className="font-bold text-slate-800">
          🔒 {isHi ? 'सुरक्षा और गोपनीयता' : 'Privacy Guarantee'}
        </p>
        <p>
          {isHi
            ? 'आपकी फ़ोटो सर्वर पर कभी सहेजी नहीं जाती। केवल ज़रूरी प्रविष्टियाँ पढ़कर तुरंत फ़ोटो हटा दी जाती है।'
            : 'Uploaded photos are never saved; only extracted fields are kept, and Aadhaar is masked.'}
        </p>
      </div>
    </div>
  );
}
