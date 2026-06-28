import { Provider } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ILlmRgpGateway } from '@domain/gateways/llm-rgp.gateway';
import { GeminiRgpAdapter } from '@infrastructure/llm/gemini-rgp.adapter';
import { ExtractRgpUseCase } from '@application/usecases/extract-rgp.usecase';

export const llmProviders: Provider[] = [
  {
    provide: ILlmRgpGateway,
    useFactory: (config: ConfigService) =>
      new GeminiRgpAdapter(
        config.get<string>('GEMINI_API_KEY', ''),
        config.get<string>('GEMINI_MODEL', 'gemini-2.5-flash'),
      ),
    inject: [ConfigService],
  },
  {
    provide: ExtractRgpUseCase,
    useFactory: (llm: ILlmRgpGateway, config: ConfigService) => new ExtractRgpUseCase(llm, config),
    inject: [ILlmRgpGateway, ConfigService],
  },
];
