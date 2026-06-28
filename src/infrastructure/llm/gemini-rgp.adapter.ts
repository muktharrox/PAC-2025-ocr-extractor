import { Injectable, Logger } from '@nestjs/common';
import { GoogleGenAI } from '@google/genai';
import { AppError } from '@application/errors/app-error';
import { ILlmRgpGateway, ILlmExtractResult } from '@domain/gateways/llm-rgp.gateway';
import { parseRgp } from '@infrastructure/schema/rgp.schema';
import { RGP_RESPONSE_SCHEMA } from './rgp.response-schema';
import { SYSTEM_PROMPT, buildUserInstruction } from './prompts/rgp.prompt';

/**
 * Implementação do gateway de LLM usando Google Gemini.
 * Envia o PDF/imagem inline (base64) e força a saída no schema estruturado.
 */
@Injectable()
export class GeminiRgpAdapter implements ILlmRgpGateway {
  private readonly logger = new Logger(GeminiRgpAdapter.name);
  private client: GoogleGenAI | null = null;

  constructor(
    private readonly apiKey: string,
    private readonly model: string,
  ) {}

  private getClient(): GoogleGenAI {
    if (!this.apiKey) throw new AppError('GEMINI_API_KEY não configurada no ambiente', 500);
    if (!this.client) {
      this.client = new GoogleGenAI({ apiKey: this.apiKey });
    }
    return this.client;
  }

  async extract(buffer: Buffer, mimeType: string, feedbackErro?: string, model?: string): Promise<ILlmExtractResult> {
    const base64 = buffer.toString('base64');

    const response = await this.getClient().models.generateContent({
      model: model || this.model,
      contents: [
        {
          role: 'user',
          parts: [{ text: buildUserInstruction(feedbackErro) }, { inlineData: { mimeType, data: base64 } }],
        },
      ],
      config: {
        systemInstruction: SYSTEM_PROMPT,
        responseMimeType: 'application/json',
        responseSchema: RGP_RESPONSE_SCHEMA,
        temperature: 0,
      },
    });

    const text = response.text;
    if (!text) {
      const reason = response.candidates?.[0]?.finishReason ?? response.promptFeedback?.blockReason ?? 'desconhecido';
      throw new AppError(`Gemini não retornou conteúdo (motivo: ${reason})`, 422);
    }

    let raw: unknown;
    try {
      raw = JSON.parse(text);
    } catch {
      this.logger.warn(`Resposta do Gemini não é JSON válido: ${text.slice(0, 200)}`);
      throw new Error('Resposta do LLM não é JSON válido');
    }

    const data = parseRgp(raw);

    const usage = response.usageMetadata;
    return {
      data,
      usage: {
        inputTokens: usage?.promptTokenCount ?? 0,
        outputTokens: usage?.candidatesTokenCount ?? 0,
      },
    };
  }
}
