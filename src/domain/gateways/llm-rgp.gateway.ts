import { IRgpCertificado } from '@domain/entities/rgp-certificado.entity';

export interface ILlmUsage {
  inputTokens: number;
  outputTokens: number;
}

export interface ILlmExtractResult {
  data: IRgpCertificado;
  usage: ILlmUsage;
}

/**
 * Porta para o LLM que extrai os dados estruturados de um certificado RGP.
 * Agnóstico de provedor — a implementação atual usa Google Gemini.
 *
 * Classe abstrata (em vez de interface) para servir de token de injeção no NestJS.
 */
export abstract class ILlmRgpGateway {
  /**
   * Extrai os dados do documento (PDF/imagem) em um único turno.
   * @param buffer conteúdo binário do arquivo
   * @param mimeType ex.: application/pdf, image/png
   * @param feedbackErro mensagem da tentativa anterior, para reforçar o prompt no retry
   */
  abstract extract(buffer: Buffer, mimeType: string, feedbackErro?: string): Promise<ILlmExtractResult>;
}
