import { IValidationResult, ok, fail } from './result';
import { isUF } from './uf';

const STRICT = /^[A-Z]{2}-\d{7}-\d$/;
// Tolerante: captura "SC 0004633 8", "sc-0004633/8", etc., evitando colar em letras/dígitos vizinhos.
const LOOSE = /(?<![A-Za-z0-9])([A-Za-z]{2})[\s\-./]*(\d{7})[\s\-./]*(\d)(?!\d)/;

/**
 * Valida e normaliza o número do RGP para o formato `UF-0000000-0`.
 * Aceita variações de separador; sinaliza por mensagem quando precisou normalizar.
 */
export function validateRgp(raw: string | null | undefined): IValidationResult {
  const value = (raw ?? '').trim();
  if (!value) return fail('RGP vazio');

  const upper = value.toUpperCase();

  if (STRICT.test(upper)) {
    const uf = upper.slice(0, 2);
    if (!isUF(uf)) return fail(`UF do RGP inválida: ${uf}`);
    return ok(upper);
  }

  const m = LOOSE.exec(value);
  if (!m) return fail('Formato de RGP não reconhecido (esperado UF-0000000-0)');

  const uf = m[1].toUpperCase();
  if (!isUF(uf)) return fail(`UF do RGP inválida: ${uf}`);

  const normalized = `${uf}-${m[2]}-${m[3]}`;
  return { valid: true, normalized, messages: [`RGP normalizado a partir de formato divergente: "${value}"`] };
}
