import { IValidationResult, ok, fail, onlyDigits } from './result';

const WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
const WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

const checkDigit = (digits: string, weights: number[]): number => {
  let total = 0;
  for (let i = 0; i < weights.length; i++) {
    total += Number(digits[i]) * weights[i];
  }
  const remainder = total % 11;
  return remainder < 2 ? 0 : 11 - remainder;
};

export const formatCnpj = (d: string): string =>
  `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12, 14)}`;

/** Valida CNPJ por módulo-11 (pesos oficiais) e retorna o valor mascarado quando válido. */
export function validateCnpj(raw: string | null | undefined): IValidationResult {
  const d = onlyDigits(raw ?? '');
  if (!d) return fail('CNPJ vazio');
  if (d.length !== 14) return fail(`CNPJ deve ter 14 dígitos (encontrado ${d.length})`);
  if (d === d[0].repeat(14)) return fail('CNPJ com todos os dígitos iguais');

  const dv1 = checkDigit(d.slice(0, 12), WEIGHTS_1);
  if (dv1 !== Number(d[12])) return fail('Primeiro dígito verificador do CNPJ inválido');

  const dv2 = checkDigit(d.slice(0, 13), WEIGHTS_2);
  if (dv2 !== Number(d[13])) return fail('Segundo dígito verificador do CNPJ inválido');

  return ok(formatCnpj(d));
}
