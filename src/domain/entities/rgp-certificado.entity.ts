export type TipoPessoa = 'PF' | 'PJ';

/**
 * Modelo plano de um Certificado de Registro Geral da Atividade Pesqueira (RGP).
 * Campos ausentes no documento devem vir como `null`. Listas vazias como `[]`.
 */
export interface IRgpCertificado {
  tipo_pessoa: TipoPessoa;

  // Cabeçalho / certificado
  numero_processo: string | null;
  ato_administrativo_concedente: string | null;
  numero_rgp: string | null;
  codigo_frota: string | null;
  inscricao_autoridade_naval: string | null;

  // Identificação e características da embarcação
  nome_embarcacao: string | null;
  ano_construcao: string | null;
  numero_tripulantes: string | null;
  comprimento_m: string | null;
  arqueacao_bruta: string | null;
  potencia_motor_hp: string | null;
  material_casco: string | null;
  propulsao: string | null;
  tipo_combustivel: string | null;

  // Modalidade de permissionamento
  metodo: string | null;
  petrecho: string | null;
  especie_alvo: string[];
  fauna_acompanhante: string[];
  autorizacao_complementar: string[];
  area_atuacao: string[];

  // Identificação do interessado (PF)
  nome: string | null;
  cpf: string | null;

  // Identificação do interessado (PJ)
  razao_social: string | null;
  cnpj: string | null;
  nome_representante_legal: string | null;
  cpf_representante_legal: string | null;

  // Endereço
  endereco: string | null;
  bairro: string | null;
  cidade_uf: string | null;

  // Despacho / validade
  data_inicio_validade: string | null;
  data_termino_validade: string | null;
}
