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
  const [processingStage, setProcessingStage] = useState(0);
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
    setProcessingStage(1);
    setErrorMessage(null);

    // Staged feedback timers
    const stageTimer1 = setTimeout(() => setProcessingStage(2), 1200);
    const stageTimer2 = setTimeout(() => setProcessingStage(3), 2500);

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
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setIsProcessing(false);
      setProcessingStage(0);
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

      {/* Realistic Passbook Viewfinder Frame */}
      {!selectedFile && (
        <Card className="relative overflow-hidden p-6 sm:p-8 text-center border-2 border-slate-300 bg-white shadow-xs">
          {/* Authentic viewfinder corner brackets */}
          <div className="absolute top-4 left-4 h-6 w-6 border-t-2 border-l-2 border-[#0f766e]" />
          <div className="absolute top-4 right-4 h-6 w-6 border-t-2 border-r-2 border-[#0f766e]" />
          <div className="absolute bottom-4 left-4 h-6 w-6 border-b-2 border-l-2 border-[#0f766e]" />
          <div className="absolute bottom-4 right-4 h-6 w-6 border-b-2 border-r-2 border-[#0f766e]" />

          {/* Passbook illustration blueprint */}
          <div className="mx-auto max-w-xs rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-5 mb-5 space-y-2">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {isHi ? 'पासबुक प्रविष्टि' : 'PASSBOOK ENTRY'}
              </span>
              <span className="text-xs">🏛️</span>
            </div>
            <div className="h-2 w-3/4 bg-slate-200 rounded" />
            <div className="h-2 w-1/2 bg-slate-200 rounded" />
            <div className="pt-2 space-y-1">
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>PMJJBY DEBIT</span>
                <span className="font-mono">₹436.00</span>
              </div>
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>PMSBY DEBIT</span>
                <span className="font-mono">₹20.00</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-base font-bold text-slate-900">
                {isHi ? 'कैमरा चालू करें या पासबुक फ़ोटो चुनें' : 'Open Camera or Choose Photo'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {isHi
                  ? 'पासबुक को समतल सतह पर रखें और साफ़ रोशनी में फ़ोटो खींचें'
                  : 'Place passbook flat under good light with all entries visible'}
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

      {/* Preview with Active Scanner HUD */}
      {selectedFile && (
        <Card className="p-4 sm:p-5 space-y-4">
          <div className="relative rounded-xl overflow-hidden bg-slate-950 aspect-4/3 flex items-center justify-center">
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

            {/* Viewfinder corner brackets on active image */}
            <div className="pointer-events-none absolute top-3 left-3 h-5 w-5 border-t-2 border-l-2 border-teal-400" />
            <div className="pointer-events-none absolute top-3 right-3 h-5 w-5 border-t-2 border-r-2 border-teal-400" />
            <div className="pointer-events-none absolute bottom-3 left-3 h-5 w-5 border-b-2 border-l-2 border-teal-400" />
            <div className="pointer-events-none absolute bottom-3 right-3 h-5 w-5 border-b-2 border-r-2 border-teal-400" />

            {/* Animated Scanning Beam during OCR */}
            {isProcessing && (
              <div className="pointer-events-none absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-teal-400 to-transparent shadow-[0_0_12px_#2dd4bf] animate-scan z-20" />
            )}
          </div>

          {/* Staged Scan Status Feedback */}
          {isProcessing ? (
            <div className="rounded-xl bg-teal-50 border border-teal-200 p-3.5 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-[#0f766e]">
                <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#0f766e] border-t-transparent" />
                <span>
                  {isHi
                    ? 'पासबुक की जाँच हो रही है...'
                    : 'Analyzing Passbook Entries...'}
                </span>
              </div>
              <div className="text-xs space-y-1 pl-5">
                <p className="text-slate-700">
                  {processingStage >= 1
                    ? isHi
                      ? '✓ छवि साफ़ प्राप्त हुई'
                      : '✓ Passbook image captured'
                    : '...'}
                </p>
                <p className={processingStage >= 2 ? 'text-slate-700' : 'text-slate-400'}>
                  {processingStage >= 2
                    ? isHi
                      ? '✓ बैंक खाता व प्रीमियम प्रविष्टियाँ पढ़ी गईं'
                      : '✓ Reading account & premium debits'
                    : isHi
                      ? '• प्रविष्टियाँ पढ़ी जा रही हैं...'
                      : '• Scanning transactions...'}
                </p>
                <p className={processingStage >= 3 ? 'text-slate-700' : 'text-slate-400'}>
                  {processingStage >= 3
                    ? isHi
                      ? '✓ सरकारी जन सुरक्षा नियमों का मिलान पूरा हुआ'
                      : '✓ Matching Jan Suraksha scheme rules'
                    : isHi
                      ? '• बीमा पात्रता जाँची जा रही है...'
                      : '• Evaluating eligibility rules...'}
                </p>
              </div>
            </div>
          ) : (
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
                {isHi ? 'बीमा खोजें →' : 'Find Covers →'}
              </Button>
            </div>
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
