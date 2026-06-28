import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AppError } from '@application/errors/app-error';
import { ILlmRgpGateway } from '@domain/gateways/llm-rgp.gateway';
import { IRgpCertificado } from '@domain/entities/rgp-certificado.entity';
import { DocumentType, IExtractResult, IFieldValidation } from '@domain/entities/extract-result.entity';
import { validateCpf } from '@infrastructure/validators/cpf';
import { validateCnpj } from '@infrastructure/validators/cnpj';
import { validateRgp } from '@infrastructure/validators/rgp';
import { validateDate, validateRange } from '@infrastructure/validators/dates';

export interface ExtractRgpInput {
  buffer: Buffer;
  filename: string;
}

interface SignatureCheck {
  mime: string;
  matches: (b: Buffer) => boolean;
}

const SIGNATURES: SignatureCheck[] = [
  { mime: 'application/pdf', matches: (b) => b.subarray(0, 5).toString('latin1') === '%PDF-' },
  {
    mime: 'image/png',
    matches: (b) => b.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])),
  },
  { mime: 'image/jpeg', matches: (b) => b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff },
  {
    mime: 'image/webp',
    matches: (b) => b.subarray(0, 4).toString('latin1') === 'RIFF' && b.subarray(8, 12).toString('latin1') === 'WEBP',
  },
];

@Injectable()
export class ExtractRgpUseCase {
  private readonly logger = new Logger(ExtractRgpUseCase.name);
  private readonly maxBytes: number;
  private readonly maxRetries: number;
  /** Cadeia de modelos: o primário seguido dos fallbacks (deduplicada, sem vazios). */
  private readonly models: string[];

  constructor(
    private readonly llm: ILlmRgpGateway,
    config: ConfigService,
  ) {
    this.maxBytes = Number(config.get('MAX_UPLOAD_MB', 20)) * 1024 * 1024;
    this.maxRetries = Number(config.get('GEMINI_MAX_RETRIES', 2));

    const primary = config.get<string>('GEMINI_MODEL', 'gemini-2.5-pro');
    // Default vazio mantém GEMINI_MAX_RETRIES como controle absoluto de tentativas.
    // O fallback de produção (gemini-2.5-flash) é definido via env (.env.example).
    const fallbacks = (config.get<string>('GEMINI_FALLBACK_MODELS', '') || '')
      .split(',')
      .map((m) => m.trim())
      .filter(Boolean);
    this.models = [...new Set([primary, ...fallbacks])];
  }

  async execute({ buffer, filename }: ExtractRgpInput): Promise<IExtractResult> {
    const start = Date.now();

    if (!buffer || buffer.length === 0) throw new AppError('Arquivo vazio', 400);
    if (buffer.length > this.maxBytes) {
      throw new AppError(`Arquivo maior que o limite de ${Math.round(this.maxBytes / 1024 / 1024)} MB`, 413);
    }

    const mimeType = this.detectMime(buffer, filename);

    let lastError: Error | null = null;
    let feedbackErro: string | undefined; // só feedback de conteúdo/parse volta para o prompt
    let modelIndex = 0;
    // Garante pelo menos uma tentativa por modelo, somadas às retentativas configuradas.
    const totalAttempts = Math.max(this.maxRetries + 1, this.models.length);
    for (let attempt = 0; attempt < totalAttempts; attempt++) {
      const model = this.models[Math.min(modelIndex, this.models.length - 1)];
      try {
        const { data, usage } = await this.llm.extract(buffer, mimeType, feedbackErro, model);
        const normalized = this.reconcileTipoPessoa(data);
        const { validations, warnings } = this.runValidators(normalized);

        return {
          success: true,
          document_type: this.docType(normalized),
          data: normalized,
          validations,
          warnings,
          processing: {
            model, // modelo que efetivamente respondeu (pode ser um fallback)
            input_tokens: usage.inputTokens,
            output_tokens: usage.outputTokens,
            pages: 1,
            used_native_text: false,
            duration_ms: Date.now() - start,
          },
        };
      } catch (err) {
        if (err instanceof AppError) throw err; // erros de negócio não são re-tentados
        lastError = err as Error;
        const transient = ExtractRgpUseCase.isTransientLlmError(lastError);
        // Erro transitório (503/429): troca para o próximo modelo de fallback, se houver.
        const switchingModel = transient && modelIndex < this.models.length - 1;
        this.logger.warn(
          `Tentativa ${attempt + 1}/${totalAttempts} (modelo ${model}) falhou` +
            `${transient ? ' (provedor de IA indisponível)' : ''}` +
            `${switchingModel ? ` — tentando fallback ${this.models[modelIndex + 1]}` : ''}: ${lastError.message}`,
        );
        if (switchingModel) modelIndex += 1;
        // Erro transitório do provedor não é feedback útil para o prompt.
        feedbackErro = transient ? undefined : lastError.message;
        if (attempt < totalAttempts - 1) {
          await this.delay(this.backoffMs(attempt, transient, switchingModel));
        }
      }
    }

    this.logger.error('Falha ao extrair RGP após retries', lastError?.stack);
    if (ExtractRgpUseCase.isTransientLlmError(lastError)) {
      throw new AppError(
        'O serviço de extração (IA) está temporariamente sobrecarregado. Aguarde alguns instantes e tente novamente.',
        503,
      );
    }
    throw new AppError('Não foi possível extrair os dados do certificado. Tente novamente.', 422);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Tempo de espera entre tentativas:
   * - ao trocar para um modelo de fallback "fresco", espera só o mínimo (o modelo
   *   novo não é o sobrecarregado, então não vale a pena aguardar);
   * - em sobrecarga do mesmo modelo, backoff exponencial com jitter (≈1s, 2s, 4s… até 8s);
   * - em erros de conteúdo/parse, backoff curto e linear.
   */
  private backoffMs(attempt: number, transient: boolean, switchingModel: boolean): number {
    if (switchingModel) return 150;
    if (!transient) return 500 * (attempt + 1);
    const exponential = Math.min(1000 * 2 ** attempt, 8000);
    const jitter = Math.floor(Math.random() * 400);
    return exponential + jitter;
  }

  /**
   * Detecta erros transitórios do provedor de IA (sobrecarga/limite de uso), que
   * devem virar 503 + nova tentativa — e NÃO 422 (que sugere documento inválido).
   * O @google/genai lança um ApiError cuja `message` é o JSON do erro
   * (ex.: {"error":{"code":503,"status":"UNAVAILABLE",...}}); por robustez também
   * cobrimos um eventual `.status`/`.code` numérico.
   */
  static isTransientLlmError(err: Error | null): boolean {
    if (!err) return false;
    const status = (err as { status?: unknown }).status ?? (err as { code?: unknown }).code;
    if (status === 503 || status === 429 || status === '503' || status === '429') return true;
    const msg = (err.message || '').toLowerCase();
    return (
      msg.includes('"code":503') ||
      msg.includes('"code":429') ||
      msg.includes('unavailable') ||
      msg.includes('overloaded') ||
      msg.includes('high demand') ||
      msg.includes('resource_exhausted') ||
      msg.includes('rate limit') ||
      msg.includes('too many requests')
    );
  }

  private detectMime(buffer: Buffer, filename: string): string {
    const found = SIGNATURES.find((s) => s.matches(buffer));
    if (found) return found.mime;
    this.logger.warn(`Assinatura de arquivo não reconhecida (${filename})`);
    throw new AppError('Formato de arquivo não suportado. Envie PDF, PNG, JPEG ou WEBP.', 415);
  }

  /** Ajusta tipo_pessoa de acordo com a presença de CNPJ/razão social vs CPF/nome. */
  private reconcileTipoPessoa(data: IRgpCertificado): IRgpCertificado {
    const hasPj = Boolean(data.cnpj || data.razao_social);
    const hasPf = Boolean(data.cpf || data.nome);
    let tipo = data.tipo_pessoa;
    if (hasPj && !hasPf) tipo = 'PJ';
    else if (hasPf && !hasPj) tipo = 'PF';
    return { ...data, tipo_pessoa: tipo };
  }

  private docType(data: IRgpCertificado): DocumentType {
    const hasPj = Boolean(data.cnpj || data.razao_social);
    const hasPf = Boolean(data.cpf || data.nome);
    if (hasPj) return 'RGP_PJ';
    if (hasPf) return 'RGP_PF';
    return 'NAO_IDENTIFICADO';
  }

  /**
   * Aplica os validadores determinísticos pós-LLM. Quando válido, sobrescreve o
   * campo em `data` com o valor normalizado (CPF/CNPJ mascarados, datas ISO).
   */
  private runValidators(data: IRgpCertificado): { validations: IFieldValidation[]; warnings: string[] } {
    const validations: IFieldValidation[] = [];
    const warnings: string[] = [];

    const apply = (
      campo: keyof IRgpCertificado,
      validate: (v: string | null) => { valid: boolean; normalized: string | null; messages: string[] },
    ) => {
      const valor = (data[campo] as string | null) ?? null;
      if (valor === null) return; // não valida campo ausente
      const r = validate(valor);
      validations.push({
        campo,
        valor,
        valido: r.valid,
        normalizado: r.normalized,
        mensagem: r.messages[0] ?? null,
      });
      if (r.valid && r.normalized) {
        (data[campo] as unknown as string) = r.normalized;
      }
      if (!r.valid) warnings.push(`Campo "${campo}" inválido: ${r.messages.join('; ')}`);
      else if (r.messages.length) warnings.push(...r.messages);
    };

    if (data.tipo_pessoa === 'PF' || data.cpf) apply('cpf', validateCpf);
    if (data.cpf_representante_legal) apply('cpf_representante_legal', validateCpf);
    if (data.tipo_pessoa === 'PJ' || data.cnpj) apply('cnpj', validateCnpj);
    if (data.numero_rgp) apply('numero_rgp', validateRgp);
    if (data.data_inicio_validade) apply('data_inicio_validade', validateDate);
    if (data.data_termino_validade) apply('data_termino_validade', validateDate);

    const range = validateRange(data.data_inicio_validade, data.data_termino_validade);
    if (!range.valid) warnings.push(range.messages.join('; '));

    return { validations, warnings };
  }
}
