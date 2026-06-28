import { IValidationResult, ok, fail } from './result';

const DMY = /^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\s*$/;
const ISO = /^\s*(\d{4})-(\d{2})-(\d{2})\s*$/;

const MIN_YEAR = 1950;
const MAX_YEAR = 2100;

const expandYear = (y: number): number => {
  if (y >= 100) return y;
  return y <= 50 ? 2000 + y : 1900 + y;
};

const pad = (n: number): string => String(n).padStart(2, '0');

/** Converte uma data (dd/mm/aaaa ou ISO) para `YYYY-MM-DD`, validando existência e faixa. */
export function validateDate(raw: string | null | undefined): IValidationResult {
  const value = (raw ?? '').trim();
  if (!value) return fail('Data vazia');

  let year: number;
  let month: number;
  let day: number;

  const iso = ISO.exec(value);
  const dmy = DMY.exec(value);

  if (iso) {
    year = Number(iso[1]);
    month = Number(iso[2]);
    day = Number(iso[3]);
  } else if (dmy) {
    day = Number(dmy[1]);
    month = Number(dmy[2]);
    year = expandYear(Number(dmy[3]));
  } else {
    return fail(`Formato de data não reconhecido: "${value}"`);
  }

  if (year < MIN_YEAR || year > MAX_YEAR) return fail(`Ano fora da faixa permitida (${MIN_YEAR}-${MAX_YEAR}): ${year}`);
  if (month < 1 || month > 12) return fail(`Mês inválido: ${month}`);
  if (day < 1 || day > 31) return fail(`Dia inválido: ${day}`);

  // Valida data realmente existente (ex.: 31/02 não existe).
  const dt = new Date(Date.UTC(year, month - 1, day));
  if (dt.getUTCFullYear() !== year || dt.getUTCMonth() !== month - 1 || dt.getUTCDate() !== day) {
    return fail(`Data inexistente: "${value}"`);
  }

  return ok(`${year}-${pad(month)}-${pad(day)}`);
}

/** Garante que início <= fim (ambos já em ISO). */
export function validateRange(inicioIso: string | null, fimIso: string | null): IValidationResult {
  if (!inicioIso || !fimIso) return ok(''); // sem ambos, nada a comparar
  if (inicioIso > fimIso) return fail(`Data de início (${inicioIso}) posterior à data de término (${fimIso})`);
  return ok('');
}
