import { IValidationResult, ok, fail, onlyDigits } from './result';

const checkDigits = (d: string): boolean => {
  for (const len of [9, 10]) {
    let total = 0;
    for (let i = 0; i < len; i++) {
      total += Number(d[i]) * (len + 1 - i);
    }
    let check = (total * 10) % 11;
    if (check === 10) check = 0;
    if (check !== Number(d[len])) return false;
  }
  return true;
};

export const formatCpf = (d: string): string => `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;

/** Valida CPF por módulo-11 e retorna o valor mascarado quando válido. */
export function validateCpf(raw: string | null | undefined): IValidationResult {
  const d = onlyDigits(raw ?? '');
  if (!d) return fail('CPF vazio');
  if (d.length !== 11) return fail(`CPF deve ter 11 dígitos (encontrado ${d.length})`);
  if (d === d[0].repeat(11)) return fail('CPF com todos os dígitos iguais');
  if (!checkDigits(d)) return fail('Dígitos verificadores do CPF inválidos');
  return ok(formatCpf(d));
}
