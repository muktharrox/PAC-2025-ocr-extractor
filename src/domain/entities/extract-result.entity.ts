import { IRgpCertificado } from './rgp-certificado.entity';

export type DocumentType = 'RGP_PF' | 'RGP_PJ' | 'NAO_IDENTIFICADO';

/** Resultado da validação determinística (mód-11 / datas) de um campo extraído. */
export interface IFieldValidation {
  campo: string;
  valor: string | null;
  valido: boolean;
  normalizado: string | null;
  mensagem: string | null;
}

/** Metadados de processamento da extração. */
export interface IProcessingMeta {
  model: string;
  input_tokens: number;
  output_tokens: number;
  pages: number;
  used_native_text: boolean;
  duration_ms: number;
}

/** Envelope de resposta da API de extração. */
export interface IExtractResult {
  success: boolean;
  document_type: DocumentType;
  data: IRgpCertificado;
  validations: IFieldValidation[];
  warnings: string[];
  processing: IProcessingMeta;
}
