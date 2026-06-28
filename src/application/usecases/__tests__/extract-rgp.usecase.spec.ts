import { ConfigService } from '@nestjs/config';
import { ExtractRgpUseCase } from '../extract-rgp.usecase';
import { AppError } from '@application/errors/app-error';
import { ILlmRgpGateway, ILlmExtractResult } from '@domain/gateways/llm-rgp.gateway';
import { IRgpCertificado } from '@domain/entities/rgp-certificado.entity';

const PDF_BYTES = Buffer.from('%PDF-1.4\n%fake pdf content for tests\n');

const baseData = (over: Partial<IRgpCertificado> = {}): IRgpCertificado => ({
  tipo_pessoa: 'PF',
  numero_processo: null,
  ato_administrativo_concedente: null,
  numero_rgp: 'SC-0001300-7',
  codigo_frota: null,
  inscricao_autoridade_naval: null,
  nome_embarcacao: 'LAGUNA',
  ano_construcao: null,
  numero_tripulantes: null,
  comprimento_m: null,
  arqueacao_bruta: null,
  potencia_motor_hp: null,
  material_casco: null,
  propulsao: null,
  tipo_combustivel: null,
  metodo: null,
  petrecho: null,
  especie_alvo: [],
  fauna_acompanhante: [],
  autorizacao_complementar: [],
  area_atuacao: [],
  nome: 'Agnaldo Medeiros Aguiar',
  cpf: '590.660.679-34',
  razao_social: null,
  cnpj: null,
  nome_representante_legal: null,
  cpf_representante_legal: null,
  endereco: null,
  bairro: null,
  cidade_uf: null,
  data_inicio_validade: '22/04/2020',
  data_termino_validade: '22/04/2025',
  ...over,
});

const makeConfig = (over: Record<string, unknown> = {}): ConfigService =>
  ({ get: (key: string, def?: unknown) => (key in over ? over[key] : def) }) as unknown as ConfigService;

const gatewayReturning = (data: IRgpCertificado): ILlmRgpGateway => ({
  extract: jest.fn(async (): Promise<ILlmExtractResult> => ({ data, usage: { inputTokens: 100, outputTokens: 50 } })),
});

describe('ExtractRgpUseCase', () => {
  it('monta envelope de sucesso PF, normaliza CPF/datas e valida', async () => {
    const useCase = new ExtractRgpUseCase(gatewayReturning(baseData()), makeConfig());
    const result = await useCase.execute({ buffer: PDF_BYTES, filename: 'laguna.pdf' });

    expect(result.success).toBe(true);
    expect(result.document_type).toBe('RGP_PF');
    expect(result.data.data_inicio_validade).toBe('2020-04-22');
    expect(result.data.data_termino_validade).toBe('2025-04-22');
    const cpfValidation = result.validations.find((v) => v.campo === 'cpf');
    expect(cpfValidation?.valido).toBe(true);
    expect(result.processing.input_tokens).toBe(100);
    expect(result.processing.output_tokens).toBe(50);
  });

  it('classifica PJ a partir de CNPJ/razão social', async () => {
    const data = baseData({
      tipo_pessoa: 'PJ',
      nome: null,
      cpf: null,
      razao_social: 'Comércio de Pescados Palhoça Ltda Me',
      cnpj: '05.383.614/0001-13',
    });
    const useCase = new ExtractRgpUseCase(gatewayReturning(data), makeConfig());
    const result = await useCase.execute({ buffer: PDF_BYTES, filename: 'lealmar.pdf' });

    expect(result.document_type).toBe('RGP_PJ');
    expect(result.validations.find((v) => v.campo === 'cnpj')?.valido).toBe(true);
  });

  it('gera warning para CPF inválido', async () => {
    const useCase = new ExtractRgpUseCase(gatewayReturning(baseData({ cpf: '111.111.111-11' })), makeConfig());
    const result = await useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' });
    expect(result.validations.find((v) => v.campo === 'cpf')?.valido).toBe(false);
    expect(result.warnings.some((w) => w.includes('cpf'))).toBe(true);
  });

  it('faz retry e resolve após falha transitória', async () => {
    let calls = 0;
    const flaky: ILlmRgpGateway = {
      extract: jest.fn(async () => {
        calls += 1;
        if (calls === 1) throw new Error('timeout transitório');
        return { data: baseData(), usage: { inputTokens: 1, outputTokens: 1 } };
      }),
    };
    const useCase = new ExtractRgpUseCase(flaky, makeConfig({ GEMINI_MAX_RETRIES: 2 }));
    const result = await useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' });
    expect(result.success).toBe(true);
    expect(calls).toBe(2);
  });

  it('mapeia sobrecarga do provedor de IA (503 UNAVAILABLE) para 503, não 422', async () => {
    const overloaded: ILlmRgpGateway = {
      extract: jest.fn(async () => {
        throw new Error(
          '{"error":{"code":503,"message":"This model is currently experiencing high demand.","status":"UNAVAILABLE"}}',
        );
      }),
    };
    const useCase = new ExtractRgpUseCase(overloaded, makeConfig({ GEMINI_MAX_RETRIES: 0 }));
    await expect(useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' })).rejects.toMatchObject({
      statusCode: 503,
    });
    expect(overloaded.extract).toHaveBeenCalledTimes(1);
  });

  it('cai para o modelo de fallback quando o primário está sobrecarregado (503)', async () => {
    const usados: string[] = [];
    const comFallback: ILlmRgpGateway = {
      extract: jest.fn(async (_buffer, _mime, _feedback, model) => {
        usados.push(model as string);
        if (model === 'gemini-2.5-flash') {
          throw new Error('{"error":{"code":503,"status":"UNAVAILABLE"}}');
        }
        return { data: baseData(), usage: { inputTokens: 10, outputTokens: 5 } };
      }),
    };
    const useCase = new ExtractRgpUseCase(
      comFallback,
      makeConfig({
        GEMINI_MODEL: 'gemini-2.5-flash',
        GEMINI_FALLBACK_MODELS: 'gemini-2.0-flash',
        GEMINI_MAX_RETRIES: 0,
      }),
    );
    const result = await useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' });

    expect(result.success).toBe(true);
    expect(usados).toEqual(['gemini-2.5-flash', 'gemini-2.0-flash']);
    expect(result.processing.model).toBe('gemini-2.0-flash');
  });

  it('mapeia falha de extração não transitória para 422', async () => {
    const failing: ILlmRgpGateway = {
      extract: jest.fn(async () => {
        throw new Error('Resposta do LLM não é JSON válido');
      }),
    };
    const useCase = new ExtractRgpUseCase(failing, makeConfig({ GEMINI_MAX_RETRIES: 0 }));
    await expect(useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' })).rejects.toMatchObject({
      statusCode: 422,
    });
  });

  it('rejeita arquivo acima do limite (413)', async () => {
    const useCase = new ExtractRgpUseCase(gatewayReturning(baseData()), makeConfig({ MAX_UPLOAD_MB: 0.00001 }));
    await expect(useCase.execute({ buffer: PDF_BYTES, filename: 'big.pdf' })).rejects.toMatchObject({
      statusCode: 413,
    });
  });

  it('rejeita assinatura de arquivo não suportada (415)', async () => {
    const useCase = new ExtractRgpUseCase(gatewayReturning(baseData()), makeConfig());
    const notAFile = Buffer.from('isto nao é um pdf nem imagem');
    await expect(useCase.execute({ buffer: notAFile, filename: 'x.txt' })).rejects.toMatchObject({
      statusCode: 415,
    });
  });

  it('propaga AppError do gateway sem retry', async () => {
    const failing: ILlmRgpGateway = {
      extract: jest.fn(async () => {
        throw new AppError('GEMINI_API_KEY não configurada no ambiente', 500);
      }),
    };
    const useCase = new ExtractRgpUseCase(failing, makeConfig());
    await expect(useCase.execute({ buffer: PDF_BYTES, filename: 'x.pdf' })).rejects.toMatchObject({
      statusCode: 500,
    });
    expect(failing.extract).toHaveBeenCalledTimes(1);
  });
});
