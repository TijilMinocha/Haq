export interface SpeechRecognitionResultLike {
  transcript: string;
}

// Browser Web Speech API definitions for TypeScript
type SpeechRecognitionType = new () => {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void) | null;
  onerror: ((event: unknown) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

function getSpeechRecognitionClass(): SpeechRecognitionType | undefined {
  if (typeof window === 'undefined') return undefined;
  const win = window as unknown as {
    SpeechRecognition?: SpeechRecognitionType;
    webkitSpeechRecognition?: SpeechRecognitionType;
  };
  return win.SpeechRecognition || win.webkitSpeechRecognition;
}

export function isSpeechRecognitionSupported(): boolean {
  return getSpeechRecognitionClass() !== undefined;
}

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

export function listenOnce(
  lang: string,
  onResult: (transcript: string) => void,
  onError?: () => void,
): () => void {
  const SpeechClass = getSpeechRecognitionClass();
  if (!SpeechClass) {
    onError?.();
    return () => {};
  }

  const recognition = new SpeechClass();
  // Match standard Indian speech recognition tags
  recognition.lang = lang === 'en' ? 'en-IN' : 'hi-IN';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const transcript = event.results[0]?.[0]?.transcript;
    if (transcript) onResult(transcript.trim());
  };

  recognition.onerror = () => {
    onError?.();
  };

  try {
    recognition.start();
  } catch {
    onError?.();
  }

  return () => {
    try {
      recognition.abort();
    } catch {
      // Ignore abort errors if already stopped
    }
  };
}

export function speak(text: string, lang: string): void {
  if (!isSpeechSynthesisSupported()) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'en' ? 'en-IN' : 'hi-IN';
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking(): void {
  if (isSpeechSynthesisSupported()) {
    window.speechSynthesis.cancel();
  }
}
