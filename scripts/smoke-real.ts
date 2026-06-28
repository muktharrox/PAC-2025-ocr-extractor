/**
 * Smoke test MANUAL contra a API Gemini real (consome cota).
 * Uso:
 *   1. Preencha GEMINI_API_KEY no .env
 *   2. Coloque um PDF em scripts/samples/ (ex.: scripts/samples/rgp.pdf)
 *   3. npm run smoke:real -- scripts/samples/rgp.pdf
 *
 * Não roda em CI. Sobe a aplicação Nest em memória e chama o use case direto.
 */
import 'reflect-metadata';
import * as fs from 'fs';
import * as path from 'path';
import { ConfigService } from '@nestjs/config';
import * as dotenv from 'dotenv';
import { GeminiRgpAdapter } from '../src/infrastructure/llm/gemini-rgp.adapter';
import { ExtractRgpUseCase } from '../src/application/usecases/extract-rgp.usecase';

dotenv.config();

async function main() {
  const file = process.argv[2] ?? path.join('scripts', 'samples', 'rgp.pdf');
  if (!fs.existsSync(file)) {
    console.error(`Arquivo não encontrado: ${file}`);
    process.exit(1);
  }

  const apiKey = process.env.GEMINI_API_KEY ?? '';
  if (!apiKey) {
    console.error('GEMINI_API_KEY não configurada (.env).');
    process.exit(1);
  }

  const model = process.env.GEMINI_MODEL ?? 'gemini-2.5-flash';
  const config = {
    get: (key: string, def?: unknown) => (process.env[key] ?? def),
  } as unknown as ConfigService;

  const adapter = new GeminiRgpAdapter(apiKey, model);
  const useCase = new ExtractRgpUseCase(adapter, config);

  const buffer = fs.readFileSync(file);
  console.log(`Enviando ${file} (${buffer.length} bytes) ao modelo ${model}...`);

  const result = await useCase.execute({ buffer, filename: path.basename(file) });
  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
