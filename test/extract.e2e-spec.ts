import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../src/presentation/modules/app.module';
import { AppErrorFilter } from '../src/presentation/filters/app-error.filter';
import { ILlmRgpGateway } from '../src/domain/gateways/llm-rgp.gateway';
import lealmar from './fixtures/rgp-pj-lealmar.json';

const PDF_BYTES = Buffer.from('%PDF-1.4\nconteudo fake de pdf para o teste e2e\n');

describe('Extract (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(ILlmRgpGateway)
      .useValue({
        extract: async () => ({ data: lealmar, usage: { inputTokens: 1200, outputTokens: 300 } }),
      })
      .compile();

    app = moduleRef.createNestApplication();
    app.setGlobalPrefix('api');
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    app.useGlobalFilters(new AppErrorFilter());
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /api/v1/health responde ok', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health').expect(200);
    expect(res.body).toEqual({ status: 'ok', service: 'pac-rgp-extractor' });
  });

  it('POST /api/v1/extract retorna o envelope estruturado (PJ)', async () => {
    const res = await request(app.getHttpServer())
      .post('/api/v1/extract')
      .attach('file', PDF_BYTES, 'lealmar.pdf')
      .expect(200);

    expect(res.body.success).toBe(true);
    expect(res.body.document_type).toBe('RGP_PJ');
    expect(res.body.data.cnpj).toBe('05.383.614/0001-13');
    expect(res.body.data.numero_rgp).toBe('SC-0004633-8');
    expect(res.body.data.data_inicio_validade).toBe('2018-11-12');
    expect(res.body.validations.find((v: any) => v.campo === 'cnpj').valido).toBe(true);
    expect(res.body.processing.model).toBeDefined();
  });

  it('POST /api/v1/extract rejeita mimetype não suportado', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/extract')
      .attach('file', Buffer.from('texto'), 'nota.txt')
      .expect(400);
  });

  it('POST /api/v1/extract exige o campo file', async () => {
    await request(app.getHttpServer()).post('/api/v1/extract').expect(400);
  });
});
