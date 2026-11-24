import { useState, type InputHTMLAttributes } from 'react';
import { useTranslation } from 'react-i18next';
import { isSpeechRecognitionSupported, listenOnce } from '@/lib/speech';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  enableVoice?: boolean;
  onVoiceInput?: (value: string) => void;
}

export function Input({
  label,
  error,
  helperText,
  enableVoice = false,
  onVoiceInput,
  id,
  className = '',
  disabled,
  ...props
}: InputProps) {
  const { i18n } = useTranslation();
  const [isListening, setIsListening] = useState(false);
  const inputId = id || label.toLowerCase().replace(/\s+/g, '-');
  const showMic = enableVoice && isSpeechRecognitionSupported() && !disabled;
  const isHi = i18n.language !== 'en';

  const handleMicClick = () => {
    if (isListening) return;
    setIsListening(true);
    listenOnce(
      i18n.language,
      (text) => {
        setIsListening(false);
        onVoiceInput?.(text);
      },
      () => setIsListening(false),
    );
  };

  return (
    <div className="w-full">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <label
          htmlFor={inputId}
          className="block text-sm font-semibold text-slate-800 leading-snug"
        >
          {label}
        </label>
        {showMic && (
          <button
            type="button"
            onClick={handleMicClick}
            aria-label={isHi ? 'बोलकर भरें' : 'Voice input'}
            className={`inline-flex shrink-0 items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg cursor-pointer transition-colors ${
              isListening
                ? 'bg-red-100 text-red-700 animate-pulse ring-1 ring-red-300'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <span>
              {isListening
                ? isHi
                  ? '🎙️ सुन रहे हैं...'
                  : '🎙️ Listening...'
                : isHi
                  ? '🎙️ बोलें'
                  : '🎙️ Speak'}
            </span>
          </button>
        )}
      </div>

      <input
        id={inputId}
        disabled={disabled}
        className={`w-full min-h-[48px] rounded-xl border px-3.5 py-2.5 text-base text-slate-900 bg-white shadow-2xs transition-colors focus:outline-none focus:ring-2 focus:ring-[#0f766e] focus:border-[#0f766e] disabled:bg-slate-50 disabled:text-slate-500 disabled:border-slate-200 ${
          error ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300'
        } ${className}`}
        {...props}
      />

      {error ? (
        <p className="mt-1 text-sm font-medium text-red-600">{error}</p>
      ) : helperText ? (
        <p className="mt-1 text-xs text-slate-500">{helperText}</p>
      ) : null}
    </div>
  );
}
