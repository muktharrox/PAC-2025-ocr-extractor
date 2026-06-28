import { IValidationResult, ok, fail } from './result';

const STRICT = /^\d{5}\.\d{6}\/\d{2}-\d{2}$/;
// Tolerante: 17 dígitos no total, com separadores variados.
const LOOSE = /(\d{5})[.\s]*(\d{6})[/\s]*(\d{2})[-\s]*(\d{2})/;

/** Valida/normaliza o número de processo para `00000.000000/00-00`. */
export function validateProcessNumber(raw: string | null | undefined): IValidationResult {
  const value = (raw ?? '').trim();
  if (!value) return fail('Número de processo vazio');

  if (STRICT.test(value)) return ok(value);

  const m = LOOSE.exec(value);
  if (!m) return fail('Formato de número de processo não reconhecido');

  const normalized = `${m[1]}.${m[2]}/${m[3]}-${m[4]}`;
  return { valid: true, normalized, messages: [`Número de processo normalizado: "${value}"`] };
}
