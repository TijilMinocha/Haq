import { describe, expect, it } from 'vitest';

import en from './locales/en.json';
import hi from './locales/hi.json';

function keys(obj: object, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    typeof v === 'object' && v !== null ? keys(v as object, `${prefix}${k}.`) : [`${prefix}${k}`],
  );
}

// Every code the server can send (plan section 5.4 and 5.5) must have text in both languages.
const SERVER_CODES = [
  'flags.name_mismatch',
  'flags.dob_mismatch',
  'flags.account_mismatch',
  'flags.nominee_missing',
  'flags.death_within_lien_period',
  'flags.rupay_no_recent_txn',
  'flags.rupay_txn_unverifiable',
  'flags.accident_docs_missing',
  'flags.claim_window_closing',
  'flags.claim_window_passed',
  'flags.ocr_low_confidence',
  'alert.cover_lapsed',
  'alert.rupay_expiring',
  'alert.nominee_missing',
  'alert.cover_active',
  'errors.validation_error',
  'errors.invalid_token',
  'errors.invalid_credentials',
  'errors.forbidden',
  'errors.too_many_attempts',
  'errors.case_not_found',
  'errors.unsupported_file',
  'errors.file_too_large',
  'errors.document_unreadable',
  'errors.form_not_applicable',
  'errors.extractor_unavailable',
];

describe('locales', () => {
  it('have the same keys in Hindi and English', () => {
    expect(keys(hi).sort()).toEqual(keys(en).sort());
  });

  it('cover every server code', () => {
    const present = new Set(keys(en));
    expect(SERVER_CODES.filter((c) => !present.has(c))).toEqual([]);
  });
});
