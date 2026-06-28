import { z } from 'zod';
import { IRgpCertificado } from '@domain/entities/rgp-certificado.entity';

/**
 * Schema Zod DEFENSIVO para validar/normalizar a saída do LLM.
 *
 * Cada campo usa `preprocess` + `.catch()` para nunca quebrar: valores
 * inesperados (número onde se espera string, string onde se espera lista, etc.)
 * são coagidos ou caem no default. Strings vazias viram `null`.
 */

// string | null tolerante (coage número→string, trim, vazio→null)
const nullableStr = z
  .preprocess((v) => {
    if (v === null || v === undefined) return null;
    const s = String(v).trim();
    return s.length ? s : null;
  }, z.string().nullable())
  .catch(null);

// string[] tolerante (item único→[item], vazio→[])
const strArray = z
  .preprocess((v) => {
    if (Array.isArray(v)) return v.map((x) => String(x).trim()).filter((s) => s.length);
    if (v === null || v === undefined) return [];
    const s = String(v).trim();
    return s.length ? [s] : [];
  }, z.array(z.string()))
  .catch([]);

const tipoPessoa = z
  .preprocess((v) => (typeof v === 'string' ? v.toUpperCase().trim() : v), z.enum(['PF', 'PJ']))
  .catch('PF');

export const RGPSchema = z.object({
  tipo_pessoa: tipoPessoa,

  numero_processo: nullableStr,
  ato_administrativo_concedente: nullableStr,
  numero_rgp: nullableStr,
  codigo_frota: nullableStr,
  inscricao_autoridade_naval: nullableStr,

  nome_embarcacao: nullableStr,
  ano_construcao: nullableStr,
  numero_tripulantes: nullableStr,
  comprimento_m: nullableStr,
  arqueacao_bruta: nullableStr,
  potencia_motor_hp: nullableStr,
  material_casco: nullableStr,
  propulsao: nullableStr,
  tipo_combustivel: nullableStr,

  metodo: nullableStr,
  petrecho: nullableStr,
  especie_alvo: strArray,
  fauna_acompanhante: strArray,
  autorizacao_complementar: strArray,
  area_atuacao: strArray,

  nome: nullableStr,
  cpf: nullableStr,
  razao_social: nullableStr,
  cnpj: nullableStr,
  nome_representante_legal: nullableStr,
  cpf_representante_legal: nullableStr,

  endereco: nullableStr,
  bairro: nullableStr,
  cidade_uf: nullableStr,

  data_inicio_validade: nullableStr,
  data_termino_validade: nullableStr,
});

export type TRgp = z.infer<typeof RGPSchema>;

// Garante em tempo de compilação que o schema cobre a entidade do domínio.
const _assertMatchesDomain: TRgp extends IRgpCertificado ? true : never = true;
void _assertMatchesDomain;

/** Faz o parse defensivo de um objeto cru vindo do LLM para `IRgpCertificado`. */
export function parseRgp(raw: unknown): IRgpCertificado {
  // RGPSchema.parse nunca lança graças aos `.catch()`; ainda assim, blindamos a entrada.
  const input = raw && typeof raw === 'object' ? raw : {};
  return RGPSchema.parse(input) as IRgpCertificado;
}
