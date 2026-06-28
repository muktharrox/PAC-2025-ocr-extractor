export interface IValidationResult {
  valid: boolean;
  normalized: string | null;
  messages: string[];
}

export const ok = (normalized: string): IValidationResult => ({ valid: true, normalized, messages: [] });

export const fail = (...messages: string[]): IValidationResult => ({ valid: false, normalized: null, messages });

export const onlyDigits = (s: string): string => (s || '').replace(/\D+/g, '');
