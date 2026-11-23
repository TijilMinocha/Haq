import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import { readJson, writeJson } from '@/lib/storage';

import en from './locales/en.json';
import hi from './locales/hi.json';

export const LANGUAGES = ['hi', 'en'] as const;
export type AppLanguage = (typeof LANGUAGES)[number];

const LANGUAGE_KEY = 'haq.language';

export function setLanguage(language: AppLanguage): void {
  writeJson(LANGUAGE_KEY, language);
  void i18n.changeLanguage(language);
  document.documentElement.lang = language;
}

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, hi: { translation: hi } },
  lng: readJson<AppLanguage>(LANGUAGE_KEY, 'hi'),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
